"""Vitrine HTML (template Stocker) + back-office session pour Comptable / Gérant."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from assistant.services import answer_question
from finance.models import Payment
from reporting.services import compute_kpis

from .forms import AssistantForm, ContactForm, EmailAuthenticationForm


def home(request):
    return render(request, "website/landing.html")


def about(request):
    return render(request, "website/about.html", {"nav": "about"})


def services(request):
    return render(request, "website/services.html", {"nav": "services"})


def faq(request):
    return render(request, "website/faq.html", {"nav": "faq"})


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        messages.success(
            request,
            "Message bien recu. Pour la demo hackathon, aucun email n'est envoye.",
        )
        return redirect("website:contact")
    return render(request, "website/contact.html", {"nav": "contact", "form": form})


class WebLoginView(LoginView):
    template_name = "website/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav"] = "login"
        return ctx


class WebLogoutView(LogoutView):
    next_page = reverse_lazy("website:home")


@login_required
def dashboard(request):
    kpis = compute_kpis()
    qs = Payment.objects.all().order_by("-paid_at")
    if not request.user.is_comptable_or_higher():
        qs = qs.filter(created_by=request.user)
    payments = qs[:12]
    answer = None
    form = AssistantForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        answer = answer_question(request.user, form.cleaned_data["question"])
    return render(
        request,
        "website/dashboard.html",
        {
            "nav": "dashboard",
            "kpis": kpis,
            "payments": payments,
            "form": form,
            "answer": answer,
        },
    )


@login_required
def payments(request):
    qs = Payment.objects.all().order_by("-paid_at")
    if not request.user.is_comptable_or_higher():
        qs = qs.filter(created_by=request.user)
    status_filter = request.GET.get("status")
    if status_filter:
        qs = qs.filter(status=status_filter)
    return render(
        request,
        "website/payments.html",
        {"nav": "payments", "payments": qs[:80], "status_filter": status_filter or ""},
    )
