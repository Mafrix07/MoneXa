"""
Finance viewsets — Invoice, Payment (with IA evidence endpoint), Account, Expense.
"""
from __future__ import annotations
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.tenancy import filter_queryset_by_org, organization_of
from accounts.permissions import (
    IsCaissierOrHigher, IsComptableOrHigher, IsGerant, IsOwnerOrComptableOrHigher,
)
from .models import (
    Account, Invoice, Payment, Expense, FinancialSource, IntegrationMethod,
    ConnectorKind, SourceStatus, Channel, MatchMethod, PaymentStatus,
)
from .serializers import (
    AccountSerializer, InvoiceSerializer, PaymentSerializer, ExpenseSerializer,
    FinancialSourceSerializer, ConnectorSyncSerializer,
)
from .services.ai_pipeline import extract_payment_from_image, extract_payment_from_text
from .services.matcher import match_payment, explain_payment
from .services.anomalies import detect_anomalies
from .services.categorize import categorize_expense
from .services.ingest import duplicate_response, existing_by_ref, ingest_normalized
from .services.sync import sync_source
from .connectors.csv_connector import CSVConnector
from .connectors.sms_connector import SMSConnector
from .connectors.manual import ManualConnector
from .connectors.base import NormalizedTransaction


class OrgMixin:
    def get_queryset(self):
        return filter_queryset_by_org(super().get_queryset(), self.request.user)


class AccountViewSet(OrgMixin, viewsets.ReadOnlyModelViewSet):
    """GET /api/accounts/ — list treasury accounts (read-only)."""
    queryset = Account.objects.filter(is_active=True).order_by("channel", "name")
    serializer_class = AccountSerializer
    permission_classes = [IsComptableOrHigher]
    filterset_fields = ["channel"]


class InvoiceViewSet(OrgMixin, viewsets.ModelViewSet):
    """
    /api/invoices/ — CRUD with role-based scoping.

    - CAISSIER sees own invoices, can create
    - COMPTABLE+ sees all
    """
    queryset = Invoice.objects.all().order_by("-issue_date")
    serializer_class = InvoiceSerializer
    permission_classes = [IsCaissierOrHigher, IsOwnerOrComptableOrHigher]
    filterset_fields = ["status", "client_name", "issue_date"]
    search_fields = ["reference", "client_name", "client_phone"]
    ordering_fields = ["issue_date", "due_date", "amount"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_comptable_or_higher():
            return qs
        return qs.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            organization=self.request.user.organization,
        )

    @action(detail=True, methods=["patch"], url_path="validate",
            permission_classes=[IsComptableOrHigher])
    def validate_invoice(self, request, pk=None):
        """Mark an invoice as RECONCILIE."""
        invoice = self.get_object()
        invoice.status = "RECONCILIE"
        invoice.save(update_fields=["status", "updated_at"])
        return Response(InvoiceSerializer(invoice).data)


class PaymentViewSet(OrgMixin, viewsets.ModelViewSet):
    """
    /api/payments/

    Endpoints:
    - GET    /payments/                  — list (CAISSIER sees own, COMPTABLE+ sees all)
    - POST   /payments/                  — manual creation
    - POST   /payments/evidence/         — upload image → IA pipeline → matcher
    - POST   /payments/manual-text/      — fallback : paste SMS text
    - PATCH  /payments/{id}/validate/    — COMPTABLE+ validates a payment
    - GET    /payments/?status=A_VALIDER — file d'attente
    """
    queryset = Payment.objects.all().order_by("-paid_at")
    serializer_class = PaymentSerializer
    permission_classes = [IsCaissierOrHigher, IsOwnerOrComptableOrHigher]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ["status", "channel", "match_method"]
    search_fields = ["provider_ref", "payer_name", "payer_phone"]
    ordering_fields = ["paid_at", "amount", "anomaly_score"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_comptable_or_higher():
            return qs
        return qs.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        with transaction.atomic():
            payment = serializer.save(created_by=self.request.user)
            # Run matcher immediately
            new_status, invoice, method = match_payment(payment)
            payment.status = new_status
            payment.match_method = method
            if invoice:
                payment.invoice = invoice
            payment.save()
            # Audit will be handled by signal

    @action(detail=False, methods=["post"], url_path="evidence",
            permission_classes=[IsCaissierOrHigher])
    def upload_evidence(self, request):
        """
        POST /api/payments/evidence/
        Upload an image of a Mobile Money receipt → run IA pipeline → create payment.

        Body: multipart/form-data with `image` file
        """
        image_file = request.FILES.get("image")
        if not image_file:
            return Response(
                {"detail": "Aucune image fournie. Champ attendu: image."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image_bytes = image_file.read()
        try:
            extracted = extract_payment_from_image(image_bytes, image_file.name)
        except Exception as e:
            return Response(
                {"detail": f"Échec de l'extraction IA: {str(e)}"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        with transaction.atomic():
            # Check for duplicate provider_ref
            existing = existing_by_ref(extracted["reference"], request.user.organization)
            if existing:
                return Response(
                    duplicate_response(existing),
                    status=status.HTTP_409_CONFLICT,
                )

            # Save image to media
            from django.core.files.base import ContentFile
            image_file.seek(0)

            payment = Payment(
                organization=request.user.organization,
                provider_ref=extracted["reference"],
                amount=extracted["montant"],
                channel=extracted["operator"],
                payer_name=extracted["emetteur"],
                payer_phone=extracted["telephone_emetteur"] or "",
                paid_at=extracted["date_paiement"],
                raw_text=extracted["raw_text"],
                ai_confidence=extracted["ai_confidence"],
                created_by=request.user,
            )
            payment.evidence_image.save(image_file.name, ContentFile(image_file.read()), save=False)
            payment.save()

            # Run matcher
            new_status, invoice, method = match_payment(payment)
            payment.status = new_status
            payment.match_method = method
            if invoice:
                payment.invoice = invoice
            payment.save()

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="manual-text",
            permission_classes=[IsCaissierOrHigher])
    def upload_manual_text(self, request):
        """
        POST /api/payments/manual-text/
        Fallback: paste SMS text directly.
        Body: {"text": "..."}
        """
        text = request.data.get("text", "").strip()
        if not text:
            return Response(
                {"detail": "Aucun texte fourni. Champ attendu: text."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            extracted = extract_payment_from_text(text)
        except Exception as e:
            return Response(
                {"detail": f"Échec de l'extraction: {str(e)}"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        with transaction.atomic():
            existing = existing_by_ref(extracted["reference"], request.user.organization)
            if existing:
                return Response(
                    duplicate_response(existing),
                    status=status.HTTP_409_CONFLICT,
                )

            payment = Payment(
                organization=request.user.organization,
                provider_ref=extracted["reference"],
                amount=extracted["montant"],
                channel=extracted["operator"],
                payer_name=extracted["emetteur"],
                payer_phone=extracted["telephone_emetteur"] or "",
                paid_at=extracted["date_paiement"],
                raw_text=extracted["raw_text"],
                ai_confidence=extracted["ai_confidence"],
                created_by=request.user,
            )
            payment.save()

            new_status, invoice, method = match_payment(payment)
            payment.status = new_status
            payment.match_method = method
            if invoice:
                payment.invoice = invoice
            payment.save()

        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="validate",
            permission_classes=[IsComptableOrHigher])
    def validate_payment(self, request, pk=None):
        """
        PATCH /api/payments/{id}/validate/
        COMPTABLE+ validates an A_VALIDER payment.
        Body: {"decision": "RECONCILIE" | "ANOMALIE"}
        """
        payment = self.get_object()
        decision = (
            request.data.get("decision")
            or request.data.get("action")
            or "RECONCILIE"
        ).upper()
        mapping = {
            "RECONCILIE": "RECONCILIE",
            "ACCEPT": "RECONCILIE",
            "APPROVE": "RECONCILIE",
            "ANOMALIE": "ANOMALIE",
            "REJECT": "ANOMALIE",
        }
        if decision not in mapping:
            return Response(
                {"detail": "decision doit être RECONCILIE/ACCEPT ou ANOMALIE/REJECT."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payment.status = mapping[decision]
        payment.match_method = MatchMethod.MANUEL if mapping[decision] else payment.match_method
        payment.save(update_fields=["status", "match_method", "updated_at"])
        return Response(PaymentSerializer(payment).data)

    @action(detail=True, methods=["get"], url_path="explain",
            permission_classes=[IsCaissierOrHigher])
    def explain(self, request, pk=None):
        """GET /api/payments/{id}/explain/ — critères réels du matcher."""
        return Response(explain_payment(self.get_object()))

    @action(detail=True, methods=["patch"], url_path="review",
            permission_classes=[IsComptableOrHigher])
    def review(self, request, pk=None):
        """
        PATCH /api/payments/{id}/review/
        Human-in-the-loop : ACCEPT | REJECT | ATTACH | REQUEST_REVIEW
        """
        payment = self.get_object()
        decision = str(request.data.get("decision") or "").upper()
        if decision in ("ACCEPT", "APPROVE", "RECONCILIE"):
            payment.status = PaymentStatus.RECONCILIE
            payment.match_method = MatchMethod.MANUEL
            payment.save(update_fields=["status", "match_method", "updated_at"])
        elif decision in ("REJECT", "ANOMALIE"):
            payment.status = PaymentStatus.ANOMALIE
            payment.save(update_fields=["status", "updated_at"])
        elif decision == "ATTACH":
            invoice_id = request.data.get("invoice_id")
            try:
                invoice = filter_queryset_by_org(Invoice.objects.all(), request.user).get(pk=invoice_id)
            except Invoice.DoesNotExist:
                return Response({"detail": "Facture introuvable."}, status=status.HTTP_404_NOT_FOUND)
            payment.invoice = invoice
            payment.status = PaymentStatus.RECONCILIE
            payment.match_method = MatchMethod.MANUEL
            payment.save(update_fields=["invoice", "status", "match_method", "updated_at"])
        elif decision == "REQUEST_REVIEW":
            payment.status = PaymentStatus.A_VALIDER
            payment.save(update_fields=["status", "updated_at"])
        else:
            return Response(
                {"detail": "decision: ACCEPT, REJECT, ATTACH ou REQUEST_REVIEW."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({
            "payment": PaymentSerializer(payment).data,
            "explain": explain_payment(payment),
        })


class ExpenseViewSet(OrgMixin, viewsets.ModelViewSet):
    """GET/POST /api/expenses/ — flux sortants."""
    queryset = Expense.objects.all().order_by("-paid_at")
    serializer_class = ExpenseSerializer
    permission_classes = [IsCaissierOrHigher, IsOwnerOrComptableOrHigher]
    filterset_fields = ["category", "paid_at"]
    search_fields = ["supplier"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_comptable_or_higher():
            return qs
        return qs.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        expense = serializer.save(
            created_by=self.request.user,
            organization=self.request.user.organization,
        )
        category = categorize_expense(
            expense.supplier, expense.note, expense.category
        )
        if category != expense.category:
            expense.category = category
            expense.save(update_fields=["category"])


class FinancialSourceViewSet(OrgMixin, viewsets.ModelViewSet):
    """
    GET/POST /api/sources/
    POST /api/sources/{id}/sync/
    GET  /api/sources/{id}/health/
    """
    queryset = FinancialSource.objects.filter(is_active=True)
    serializer_class = FinancialSourceSerializer
    permission_classes = [IsComptableOrHigher]
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action in ("create", "sync"):
            return [IsGerant()]
        return [IsComptableOrHigher()]

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            is_simulated=True,
            organization=self.request.user.organization,
        )

    @action(detail=True, methods=["post"], url_path="sync")
    def sync(self, request, pk=None):
        source = self.get_object()
        log = sync_source(source, request.user)
        return Response({
            "source": FinancialSourceSerializer(source).data,
            "sync": ConnectorSyncSerializer(log).data,
            "disclaimer": "Synchronisation via connecteur simulé. Aucune API opérateur réelle.",
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="health")
    def health(self, request, pk=None):
        from finance.connectors.registry import get_connector
        source = self.get_object()
        connector = get_connector(source.connector_kind)
        payload = connector.health_check()
        payload["source_id"] = source.id
        payload["last_sync_at"] = source.last_sync_at
        payload["last_error"] = source.last_error
        return Response(payload)


class EvidenceView(APIView):
    """
    POST /api/evidence/ — point d'entrée unique (photo, SMS, CSV, saisie).
    N'atteste pas l'authenticité de la preuve.
    """
    permission_classes = [IsCaissierOrHigher]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        kind = str(request.data.get("kind") or request.data.get("type") or "").lower()
        user = request.user
        try:
            if kind in ("image", "photo", "capture"):
                image_file = request.FILES.get("image") or request.FILES.get("file")
                if not image_file:
                    return Response({"detail": "Fichier image manquant."}, status=400)
                extracted = extract_payment_from_image(image_file.read(), image_file.name)
                tx = NormalizedTransaction(
                    source=extracted["operator"],
                    external_id=extracted["reference"],
                    direction="IN",
                    amount=extracted["montant"],
                    currency="XOF",
                    counterparty=extracted["emetteur"],
                    reference=extracted["reference"],
                    occurred_at=extracted["date_paiement"],
                    phone=extracted.get("telephone_emetteur") or "",
                    raw_payload={"raw_text": extracted.get("raw_text", "")},
                )
            elif kind == "sms":
                text = (request.data.get("text") or "").strip()
                if not text:
                    return Response({"detail": "Champ text manquant."}, status=400)
                tx = SMSConnector(text).normalize(text)
            elif kind in ("csv", "excel"):
                upload = request.FILES.get("file") or request.FILES.get("csv")
                if not upload:
                    return Response({"detail": "Fichier CSV manquant."}, status=400)
                connector = CSVConnector(upload.read())
                rows, _ = connector.fetch_transactions()
                created, ignored = [], []
                for row in rows:
                    ntx = connector.normalize(row)
                    existing = existing_by_ref(ntx.reference, request.user.organization)
                    if existing:
                        ignored.append(duplicate_response(existing))
                        continue
                    payment, _ = ingest_normalized(ntx, user)
                    created.append(PaymentSerializer(payment).data)
                return Response({
                    "kind": "csv",
                    "created": created,
                    "ignored": ignored,
                    "disclaimer": "Import fichier. Pas une preuve d'authenticité.",
                }, status=201)
            elif kind == "manual":
                tx = ManualConnector().normalize(request.data)
            else:
                return Response(
                    {"detail": "kind doit être image, sms, csv ou manual."},
                    status=400,
                )
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        existing = existing_by_ref(tx.reference, request.user.organization)
        if existing:
            return Response(duplicate_response(existing), status=status.HTTP_409_CONFLICT)

        payment, _ = ingest_normalized(tx, user)
        return Response({
            "kind": kind,
            "payment": PaymentSerializer(payment).data,
            "explain": explain_payment(payment),
            "extracted": {
                "amount": str(tx.amount),
                "reference": tx.reference,
                "counterparty": tx.counterparty,
                "source": tx.source,
                "occurred_at": tx.occurred_at.isoformat(),
            },
            "disclaimer": (
                "Données extraites et rapprochées des factures internes. "
                "Ce n'est pas une preuve d'authenticité de la capture."
            ),
        }, status=status.HTTP_201_CREATED)

