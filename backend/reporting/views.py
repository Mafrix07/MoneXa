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
from finance.models import Payment, Expense, ForecastCache
from finance.services.forecast import forecast_cashflow
from finance.services.anomalies import detect_anomalies, score_isolation_forest
from auditing.models import AuditLog
from auditing.serializers import AuditLogSerializer
from .services import compute_kpis
from .serializers import KPISerializer


class DashboardSummaryView(APIView):
    """GET /api/dashboard/summary/ — KPIs agrégés par canal."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        kpis = compute_kpis()
        return Response(kpis)


class ForecastView(APIView):
    """GET /api/reports/forecast/?days=30 — Holt-Winters prévisions."""
    permission_classes = [IsComptableOrHigher]

    def get(self, request):
        days = int(request.query_params.get("days", 30))
        if days not in (7, 30):
            days = 30
        # Try cached
        try:
            cached = ForecastCache.objects.get(days=days)
            return Response({
                "days": days,
                "forecast": cached.forecast_data,
                "confidence_low": cached.confidence_low,
                "confidence_high": cached.confidence_high,
                "model": "Holt-Winters (cached)",
                "generated_at": cached.generated_at,
            })
        except ForecastCache.DoesNotExist:
            forecast = forecast_cashflow(days=days)
            return Response(forecast)


class AnomaliesView(APIView):
    """GET /api/anomalies/ — liste des anomalies (GERANT seulement)."""
    permission_classes = [IsGerant]

    def get(self, request):
        # Récupère paiements en anomalie
        anomalies_payments = Payment.objects.filter(status="ANOMALIE").order_by("-paid_at")[:50]
        result = []
        for p in anomalies_payments:
            for a in detect_anomalies(p):
                result.append({
                    "payment_id": p.id,
                    "provider_ref": p.provider_ref,
                    "amount": float(p.amount),
                    "channel": p.channel,
                    "paid_at": p.paid_at.isoformat(),
                    **a,
                })

        # Add Isolation Forest flagged payments
        iflagged = score_isolation_forest()
        return Response({
            "rule_based_anomalies": result,
            "ml_flagged_payments": iflagged,
            "total": len(result) + len(iflagged),
        })


class AuditLogListView(generics.ListAPIView):
    """GET /api/audit-logs/ — Journal immuable (GERANT seulement)."""
    queryset = AuditLog.objects.all().order_by("-timestamp")
    serializer_class = AuditLogSerializer
    permission_classes = [IsGerant]

    def get_queryset(self):
        qs = super().get_queryset()
        # Optional filtering
        action = self.request.query_params.get("action")
        if action:
            qs = qs.filter(action=action)
        return qs


class ExportView(APIView):
    """GET /api/reports/export/?format=csv&model=payments — Export Excel/CSV."""
    permission_classes = [IsComptableOrHigher]

    def get(self, request):
        fmt = request.query_params.get("format", "csv").lower()
        model = request.query_params.get("model", "payments").lower()

        if fmt != "csv":
            return Response(
                {"detail": "Format non supporté. Utilisez ?format=csv."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if model == "payments":
            queryset = Payment.objects.all().order_by("-paid_at")
            rows = self._payments_to_rows(queryset)
        elif model == "expenses":
            queryset = Expense.objects.all().order_by("-paid_at")
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
