from django.urls import path

from . import views

app_name = "website"

urlpatterns = [
    path("", views.home, name="home"),
    path("a-propos/", views.about, name="about"),
    path("fonctionnalites/", views.services, name="services"),
    path("faq/", views.faq, name="faq"),
    path("contact/", views.contact, name="contact"),
    path("connexion/", views.WebLoginView.as_view(), name="login"),
    path("deconnexion/", views.WebLogoutView.as_view(), name="logout"),
    path("tableau-de-bord/", views.dashboard, name="dashboard"),
    path("tresorerie/", views.treasury, name="treasury"),
    path("paiements/", views.payments, name="payments"),
    path("paiements/<int:pk>/", views.payment_detail, name="payment_detail"),
    path("paiements/<int:pk>/review/", views.payment_review, name="payment_review"),
    path("factures/", views.invoices, name="invoices"),
    path("factures/nouvelle/", views.invoice_create, name="invoice_create"),
    path("factures/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("rapprochement/", views.reconciliation, name="reconciliation"),
    path("anomalies/", views.anomalies, name="anomalies"),
    path("previsions/", views.forecast, name="forecast"),
    path("sources/", views.sources, name="sources"),
    path("sources/<int:pk>/sync/", views.source_sync, name="source_sync"),
    path("sources/jeton-caisse/", views.pos_token_create, name="pos_token_create"),
    path("sources/jeton-caisse/<int:pk>/revoquer/", views.pos_token_revoke, name="pos_token_revoke"),
    path("tresoria/", views.assistant, name="assistant"),
    path("preuves/", views.evidence, name="evidence"),
    path("utilisateurs/", views.users_page, name="users"),
    path("audit/", views.audit, name="audit"),
]
