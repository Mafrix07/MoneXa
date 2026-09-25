"""Vitrine + espace métier web. Lecture des services existants, pas de nouvelle logique financière."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.tenancy import filter_queryset_by_org
from assistant.services import answer_question
from auditing.models import AuditLog
from finance.models import (
    Account,
    Channel,
    FinancialSource,
    Invoice,
    MatchMethod,
    Payment,
    PaymentStatus,
)
from finance.services.anomalies import detect_anomalies
from finance.services.forecast import forecast_cashflow
from finance.services.ingest import duplicate_response, existing_by_ref
from finance.services.matcher import explain_payment, match_payment
from finance.services.sync import sync_source
from reporting.services import compute_kpis, explain_forecast

from .forms import AssistantForm, ContactForm, EmailAuthenticationForm, EvidenceTextForm


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
            "Message bien reçu. Nous vous recontactons si un canal e-mail est configuré.",
        )
        return redirect("website:contact")
    return render(request, "website/contact.html", {"nav": "contact", "form": form})


class WebLoginView(LoginView):
    template_name = "website/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("website:dashboard")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["nav"] = "login"
        return ctx


class WebLogoutView(LogoutView):
    next_page = reverse_lazy("website:home")


def _payments_qs(request):
    qs = filter_queryset_by_org(Payment.objects.all().order_by("-paid_at"), request.user)
    if not request.user.is_comptable_or_higher():
        qs = qs.filter(created_by=request.user)
    return qs


def _invoices_qs(request):
    qs = filter_queryset_by_org(Invoice.objects.all().order_by("-issue_date"), request.user)
    if not request.user.is_comptable_or_higher():
        qs = qs.filter(created_by=request.user)
    return qs


def _spark(values, width=640, height=140):
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        x = (i / max(n - 1, 1)) * width
        y = height - ((v - lo) / span) * (height - 12) - 6
        pts.append(f"{x:.1f},{y:.1f}")
    return "M " + " L ".join(pts)


@login_required
def dashboard(request):
    kpis = compute_kpis(organization=request.user.organization)
    payments = _payments_qs(request)[:8]
    answer = None
    form = AssistantForm(request.POST or None)
    if request.method == "POST" and form.is_valid() and request.POST.get("ask"):
        answer = answer_question(request.user, form.cleaned_data["question"])
    first = (request.user.first_name or request.user.display_name or "").split("@")[0]
    return render(
        request,
        "website/dashboard.html",
        {
            "nav": "dashboard",
            "kpis": kpis,
            "payments": payments,
            "form": form,
            "answer": answer,
            "hello_name": first,
            "channels": Channel.choices,
        },
    )


@login_required
def treasury(request):
    kpis = compute_kpis(organization=request.user.organization)
    sources = filter_queryset_by_org(FinancialSource.objects.filter(is_active=True), request.user)
    return render(
        request,
        "website/treasury.html",
        {"nav": "treasury", "kpis": kpis, "sources": sources, "channels": Channel.choices},
    )


@login_required
def payments(request):
    qs = _payments_qs(request)
    status_filter = request.GET.get("status") or ""
    q = (request.GET.get("q") or "").strip()
    channel = request.GET.get("channel") or ""
    if status_filter:
        qs = qs.filter(status=status_filter)
    if channel:
        qs = qs.filter(channel=channel)
    if q:
        qs = qs.filter(Q(provider_ref__icontains=q) | Q(payer_name__icontains=q))
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(
        request,
        "website/payments.html",
        {
            "nav": "payments",
            "page": page,
            "payments": page.object_list,
            "status_filter": status_filter,
            "q": q,
            "channel": channel,
            "channels": Channel.choices,
        },
    )


@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(_payments_qs(request), pk=pk)
    explain = explain_payment(payment)
    audits = AuditLog.objects.filter(entity="Payment", entity_id=str(payment.pk)).order_by("-timestamp")[:20]
    if request.user.organization_id:
        audits = audits.filter(organization_id=request.user.organization_id)
    pending = []
    if request.user.is_comptable_or_higher():
        pending = list(_invoices_qs(request).filter(status="EN_ATTENTE")[:40])
    return render(
        request,
        "website/payment_detail.html",
        {
            "nav": "payments",
            "payment": payment,
            "explain": explain,
            "audits": audits,
            "pending_invoices": pending,
        },
    )


@login_required
@require_POST
def payment_review(request, pk):
    if not request.user.is_comptable_or_higher():
        return HttpResponseForbidden()
    payment = get_object_or_404(_payments_qs(request), pk=pk)
    decision = str(request.POST.get("decision") or "").upper()
    if decision in ("ACCEPT", "APPROVE"):
        payment.status = PaymentStatus.RECONCILIE
        payment.match_method = MatchMethod.MANUEL
        payment.save(update_fields=["status", "match_method", "updated_at"])
        messages.success(request, "Rapprochement accepté.")
    elif decision in ("REJECT",):
        payment.status = PaymentStatus.ANOMALIE
        payment.save(update_fields=["status", "updated_at"])
        messages.success(request, "Rapprochement refusé — marqué en anomalie.")
    elif decision == "ATTACH":
        invoice = get_object_or_404(_invoices_qs(request), pk=request.POST.get("invoice_id"))
        payment.invoice = invoice
        payment.status = PaymentStatus.RECONCILIE
        payment.match_method = MatchMethod.MANUEL
        payment.save(update_fields=["invoice", "status", "match_method", "updated_at"])
        messages.success(request, f"Rattaché à {invoice.reference}.")
    else:
        messages.error(request, "Action non reconnue.")
    return redirect("website:payment_detail", pk=payment.pk)


@login_required
def invoices(request):
    qs = _invoices_qs(request)
    status_filter = request.GET.get("status") or ""
    if status_filter:
        qs = qs.filter(status=status_filter)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(
        request,
        "website/invoices.html",
        {"nav": "invoices", "page": page, "invoices": page.object_list, "status_filter": status_filter},
    )


@login_required
def reconciliation(request):
    if not request.user.is_comptable_or_higher():
        return HttpResponseForbidden()
    qs = _payments_qs(request).filter(status=PaymentStatus.A_VALIDER)
    items = []
    for p in qs[:30]:
        items.append({"payment": p, "explain": explain_payment(p)})
    return render(request, "website/reconciliation.html", {"nav": "reconciliation", "items": items})


@login_required
def anomalies(request):
    if not request.user.is_comptable_or_higher():
        return HttpResponseForbidden()
    qs = _payments_qs(request).filter(status__in=["ANOMALIE", "NON_RATTACHE"])[:60]
    rows = []
    for p in qs:
        flags = detect_anomalies(p)
        rows.append({"payment": p, "flags": flags})
    return render(request, "website/anomalies.html", {"nav": "anomalies", "rows": rows})


@login_required
def forecast(request):
    if not request.user.is_comptable_or_higher():
        return HttpResponseForbidden()
    org = request.user.organization
    data = forecast_cashflow(days=30, organization=org)
    explanation = explain_forecast(days=30, organization=org)
    pts = explanation.get("points") or {}
    checkpoints = [
        ("Aujourd'hui", pts.get("today")),
        ("J+7", pts.get("j7")),
        ("J+15", pts.get("j15")),
        ("J+30", pts.get("j30")),
    ]
    return render(
        request,
        "website/forecast.html",
        {
            "nav": "forecast",
            "data": data,
            "explanation": explanation,
            "spark": _spark(data.get("forecast") or []),
            "checkpoints": checkpoints,
            "insufficient": "insufficient" in (data.get("model") or "").lower(),
        },
    )


@login_required
def sources(request):
    if not request.user.is_comptable_or_higher():
        return HttpResponseForbidden()
    kpis = compute_kpis(organization=request.user.organization)
    srcs = filter_queryset_by_org(FinancialSource.objects.all(), request.user)
    accounts = filter_queryset_by_org(Account.objects.filter(is_active=True), request.user)
    return render(
        request,
        "website/sources.html",
        {
            "nav": "sources",
            "sources": srcs,
            "accounts": accounts,
            "solde_par_canal": kpis.get("solde_par_canal") or {},
        },
    )


@login_required
@require_POST
def source_sync(request, pk):
    if not request.user.is_comptable_or_higher():
        return HttpResponseForbidden()
    source = get_object_or_404(
        filter_queryset_by_org(FinancialSource.objects.all(), request.user), pk=pk
    )
    log = sync_source(source, request.user)
    messages.success(
        request,
        f"Synchronisation {log.status} — {log.created_count} créée(s), {log.ignored_count} ignorée(s).",
    )
    return redirect("website:sources")


@login_required
def assistant(request):
    form = AssistantForm(request.POST or None)
    answer = None
    question = ""
    if request.method == "POST" and form.is_valid():
        question = form.cleaned_data["question"]
        answer = answer_question(request.user, question)
    kpis = compute_kpis(organization=request.user.organization)
    return render(
        request,
        "website/assistant.html",
        {"nav": "assistant", "form": form, "answer": answer, "question": question, "kpis": kpis},
    )


@login_required
def evidence(request):
    form = EvidenceTextForm(request.POST or None)
    extracted = None
    if request.method == "POST" and form.is_valid():
        from finance.services.ai_pipeline import extract_payment_from_text

        text = form.cleaned_data["text"]
        try:
            extracted = extract_payment_from_text(text)
        except Exception:
            messages.error(
                request,
                "Extraction temporairement indisponible. Vous pouvez saisir les informations manuellement.",
            )
            extracted = None
        else:
            if request.POST.get("confirm"):
                existing = existing_by_ref(extracted["reference"], request.user.organization)
                if existing:
                    messages.error(request, duplicate_response(existing)["detail"])
                else:
                    from django.db import transaction

                    with transaction.atomic():
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
                    messages.success(request, f"Preuve enregistrée ({payment.provider_ref}).")
                    return redirect("website:payment_detail", pk=payment.pk)
    return render(
        request,
        "website/evidence.html",
        {"nav": "evidence", "form": form, "extracted": extracted},
    )


@login_required
def users_page(request):
    if not request.user.is_gerant():
        return HttpResponseForbidden()
    members = User.objects.filter(organization=request.user.organization).order_by("email")
    return render(request, "website/users.html", {"nav": "users", "members": members})


@login_required
def audit(request):
    if not request.user.is_gerant():
        return HttpResponseForbidden()
    qs = filter_queryset_by_org(AuditLog.objects.all().order_by("-timestamp"), request.user)
    page = Paginator(qs, 40).get_page(request.GET.get("page"))
    return render(request, "website/audit.html", {"nav": "audit", "page": page, "logs": page.object_list})
