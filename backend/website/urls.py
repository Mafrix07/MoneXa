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
    path("paiements/", views.payments, name="payments"),
]
