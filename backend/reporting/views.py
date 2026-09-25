"""
Reporting views — dashboard, forecast, anomalies, audit logs, exports.
"""
from __future__ import annotations
import csv
import io
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsComptableOrHigher, IsGerant
from accounts.tenancy import filter_queryset_by_org
from finance.models import Payment, Expense, ForecastCache
from finance.services.forecast import forecast_cashflow
from finance.services.anomalies import detect_anomalies, score_isolation_forest
from auditing.models import AuditLog
from auditing.serializers import AuditLogSerializer
from .services import compute_kpis, explain_forecast
from .serializers import KPISerializer


class DashboardSummaryView(APIView):
    """GET /api/dashboard/summary/ — KPIs agrégés par canal."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        kpis = compute_kpis(organization=request.user.organization)
        return Response(kpis)


class ForecastView(APIView):
    """GET /api/reports/forecast/?days=30 — Holt-Winters prévisions."""
    permission_classes = [IsComptableOrHigher]

    def get(self, request):
        org = request.user.organization
        days = int(request.query_params.get("days", 30))
        if days not in (7, 30):
            days = 30
        fc = ForecastCache.objects.filter(days=days)
        if org is not None:
            fc = fc.filter(organization=org)
        cached = fc.first()
        if cached:
            return Response({
                "days": days,
                "forecast": cached.forecast_data,
                "confidence_low": cached.confidence_low,
                "confidence_high": cached.confidence_high,
                "model": "Holt-Winters (cached)",
                "generated_at": cached.generated_at,
                "explanation": explain_forecast(days=days, organization=org),
            })
        forecast = forecast_cashflow(days=days, organization=org)
        forecast["explanation"] = explain_forecast(days=days, organization=org)
        return Response(forecast)


class AnomaliesView(APIView):
    """GET /api/anomalies/ — centre Guard (Gérant). Jamais le mot « fraude » auto."""
    permission_classes = [IsGerant]

    def get(self, request):
        grouped = {
            "doublon_potentiel": [],
            "paiement_non_rattache": [],
            "montant_incoherent": [],
            "anomalie_comportementale": [],
        }
        qs = Payment.objects.filter(
            status__in=["ANOMALIE", "NON_RATTACHE"]
        ).order_by("-paid_at")
        qs = filter_queryset_by_org(qs, request.user)[:80]
        seen = set()
        for p in qs:
            for a in detect_anomalies(p):
                item = {
                    "payment_id": p.id,
                    "provider_ref": p.provider_ref,
                    "amount": float(p.amount),
                    "channel": p.channel,
                    "paid_at": p.paid_at.isoformat(),
                    "label": "Anomalie détectée",
                    **a,
                }
                key = (p.id, a.get("type"))
                if key in seen:
                    continue
                seen.add(key)
                t = (a.get("type") or "").lower()
                if "écart" in t or "ecart" in t:
                    grouped["montant_incoherent"].append(item)
                elif "sans facture" in t or "non rattach" in t:
                    grouped["paiement_non_rattache"].append(item)
                elif "nocturne" in t or "fenêtre" in t or "fenetre" in t:
                    grouped["anomalie_comportementale"].append(item)
                else:
                    grouped["anomalie_comportementale"].append(item)

        iflagged = score_isolation_forest(organization=request.user.organization)
        for row in iflagged:
            row["label"] = "Anomalie détectée"
            row["type"] = "Score comportemental (Isolation Forest)"
            grouped["anomalie_comportementale"].append(row)

        total = sum(len(v) for v in grouped.values())
        return Response({
            "categories": grouped,
            "total": total,
            "disclaimer": (
                "Détection de cohérence interne et d'atypie statistique. "
                "Ce n'est pas une qualification de fraude."
            ),
        })


class AuditLogListView(generics.ListAPIView):
    """GET /api/audit-logs/ — Journal immuable (GERANT seulement)."""
    queryset = AuditLog.objects.all().order_by("-timestamp")
    serializer_class = AuditLogSerializer
    permission_classes = [IsGerant]

    def get_queryset(self):
        qs = super().get_queryset()
        return filter_queryset_by_org(qs, self.request.user)


class ExportView(APIView):
    """GET /api/reports/export/?export_format=csv&model=payments — Export Excel/CSV."""
    permission_classes = [IsComptableOrHigher]

    def get(self, request):
        fmt = request.query_params.get("export_format", "csv").lower()
        model = request.query_params.get("model", "payments").lower()

        if fmt != "csv":
            return Response(
                {"detail": "Format non supporté. Utilisez ?format=csv."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if model == "payments":
            queryset = filter_queryset_by_org(Payment.objects.all().order_by("-paid_at"), request.user)
            rows = self._payments_to_rows(queryset)
        elif model == "expenses":
            queryset = filter_queryset_by_org(Expense.objects.all().order_by("-paid_at"), request.user)
            rows = self._expenses_to_rows(queryset)
        else:
            return Response(
                {"detail": "Modèle non supporté. Utilisez ?model=payments ou ?model=expenses."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";")
        if rows:
            writer.writerow(rows[0].keys())
            for row in rows:
                writer.writerow(row.values())

        from django.http import HttpResponse
        response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="monexa_{model}.csv"'
        return response

    def _payments_to_rows(self, queryset):
        return [
            {
                "provider_ref": p.provider_ref,
                "amount": float(p.amount),
                "channel": p.channel,
                "payer_name": p.payer_name,
                "payer_phone": p.payer_phone,
                "paid_at": p.paid_at.isoformat(),
                "status": p.status,
                "match_method": p.match_method,
                "ai_confidence": p.ai_confidence,
                "anomaly_score": p.anomaly_score,
            }
            for p in queryset
        ]

    def _expenses_to_rows(self, queryset):
        return [
            {
                "supplier": e.supplier,
                "category": e.category,
                "amount": float(e.amount),
                "paid_at": e.paid_at.isoformat(),
            }
            for e in queryset
        ]
