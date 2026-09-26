"""API caisse : Bearer mxpos_live_* → factures et paiements."""
from __future__ import annotations

from django.utils import timezone as dj_timezone
from rest_framework import status
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.serializers import InvoiceSerializer, PaymentSerializer
from finance.services.ingest import duplicate_response
from finance.services.pos import ingest_pos_invoice, ingest_pos_payment, resolve_pos_token


class PosTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = request.META.get("HTTP_AUTHORIZATION") or ""
        if not header.lower().startswith("bearer "):
            return None
        raw = header.split(" ", 1)[1].strip()
        if not raw.startswith("mxpos_live_"):
            return None
        cred = resolve_pos_token(raw)
        if cred is None:
            raise AuthenticationFailed("Jeton caisse invalide ou révoqué.")
        request.pos_credential = cred
        cred.last_used_at = dj_timezone.now()
        cred.save(update_fields=["last_used_at"])
        return (cred.created_by, cred)

    def authenticate_header(self, request):
        return "Bearer"


class PosBaseView(APIView):
    authentication_classes = [PosTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def credential(self, request):
        return getattr(request, "pos_credential", None)


class PosPingView(PosBaseView):
    def get(self, request):
        cred = self.credential(request)
        return Response({
            "ok": True,
            "organization": cred.organization.name if cred else "",
            "channel": cred.channel if cred else "",
            "name": cred.name if cred else "",
        })


class PosInvoiceView(PosBaseView):
    def post(self, request):
        cred = self.credential(request)
        try:
            invoice, created = ingest_pos_invoice(cred, request.data)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        data = InvoiceSerializer(invoice).data
        return Response(
            {"created": created, "invoice": data, "monexa_ref": invoice.monexa_ref, "reference": invoice.reference},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class PosPaymentView(PosBaseView):
    def post(self, request):
        cred = self.credential(request)
        try:
            payment, created = ingest_pos_payment(cred, request.data)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if not created:
            return Response(duplicate_response(payment), status=status.HTTP_409_CONFLICT)
        return Response(
            {"created": True, "payment": PaymentSerializer(payment).data},
            status=status.HTTP_201_CREATED,
        )
