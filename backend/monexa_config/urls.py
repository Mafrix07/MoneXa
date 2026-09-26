"""
URL configuration MoneXa — API REST + Django Admin + Swagger.
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from accounts.viewsets import MeViewSet, UserViewSet
from accounts.views import (
    MonexaTokenObtainPairView,
    OrganizationMeView,
    RegisterView,
    Toggle2FAView,
)
from finance.pos_api import PosInvoiceView, PosPaymentView, PosPingView
from finance.viewsets import (
    AccountViewSet,
    InvoiceViewSet,
    PaymentViewSet,
    ExpenseViewSet,
    FinancialSourceViewSet,
    EvidenceView,
)
from reporting.views import (
    DashboardSummaryView,
    ForecastView,
    AnomaliesView,
    AuditLogListView,
    ExportView,
)
from assistant.views import AskView
from monexa_config.health import health, ready

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"accounts", AccountViewSet, basename="account")
router.register(r"invoices", InvoiceViewSet, basename="invoice")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"expenses", ExpenseViewSet, basename="expense")
router.register(r"sources", FinancialSourceViewSet, basename="source")

urlpatterns = [
    path("", include("website.urls")),
    path("health/", health, name="health"),
    path("ready/", ready, name="ready"),

    # Admin
    path("admin/", admin.site.urls),

    # Auth
    path("api/auth/register/", RegisterView.as_view(), name="auth_register"),
    path("api/auth/token/", MonexaTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/auth/me/", MeViewSet.as_view({"get": "retrieve"}), name="auth_me"),
    path("api/auth/me/2fa/", Toggle2FAView.as_view(), name="auth_me_2fa"),
    path("api/organizations/me/", OrganizationMeView.as_view(), name="organization_me"),

    # API REST
    path("api/", include(router.urls)),

    # Reporting & dashboard
    path("api/dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard_summary"),
    path("api/reports/forecast/", ForecastView.as_view(), name="reports_forecast"),
    path("api/reports/export/", ExportView.as_view(), name="reports_export"),
    path("api/anomalies/", AnomaliesView.as_view(), name="anomalies_list"),
    path("api/audit-logs/", AuditLogListView.as_view(), name="audit_logs_list"),

    # Assistant TresorIA
    path("api/assistant/ask/", AskView.as_view(), name="assistant_ask"),
    path("api/evidence/", EvidenceView.as_view(), name="evidence"),
    path("api/pos/v1/ping/", PosPingView.as_view(), name="pos_ping"),
    path("api/pos/v1/invoices/", PosInvoiceView.as_view(), name="pos_invoices"),
    path("api/pos/v1/payments/", PosPaymentView.as_view(), name="pos_payments"),

    # Documentation API
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger_ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]
