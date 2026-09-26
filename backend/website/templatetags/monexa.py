from decimal import Decimal, InvalidOperation

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_STATUS = {
    "RECONCILIE": ("ok", "Validé"),
    "A_VALIDER": ("warn", "À valider"),
    "ANOMALIE": ("danger", "Anomalie"),
    "NON_RATTACHE": ("info", "Non rattaché"),
    "EN_ATTENTE": ("warn", "En attente"),
    "EMISE": ("warn", "Émise"),
    "PARTIELLEMENT_PAYEE": ("warn", "Partiellement payée"),
    "PAYEE": ("ok", "Payée"),
    "EN_RETARD": ("danger", "En retard"),
    "ANNULEE": ("muted", "Annulée"),
    "ANNULE": ("muted", "Annulé"),
    "BROUILLON": ("muted", "Brouillon"),
    "ACTIVE": ("ok", "Actif"),
    "IDLE": ("muted", "En attente"),
    "ERROR": ("danger", "Erreur"),
    "DISABLED": ("muted", "Désactivé"),
    "SUCCESS": ("ok", "Succès"),
    "PARTIAL": ("warn", "Partiel"),
    "RUNNING": ("info", "En cours"),
}


@register.filter
def money(value):
    if value is None or value == "":
        return "—"
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return "—"
    if n == n.to_integral_value():
        formatted = f"{int(n):,}".replace(",", " ")
    else:
        formatted = f"{n:,.2f}".replace(",", " ").replace(".", ",")
    return f"{formatted} FCFA"


@register.filter
def lookup(mapping, key):
    if not mapping:
        return None
    try:
        return mapping.get(key)
    except AttributeError:
        return None


@register.filter
def money_signed(value):
    if value is None or value == "":
        return "—"
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return "—"
    sign = "+" if n >= 0 else "−"
    return f"{sign}{money(abs(n))}"


@register.simple_tag
def status_badge(code, label=None):
    tone, default = _STATUS.get(str(code or ""), ("muted", str(code or "—")))
    text = label or default
    return mark_safe(
        f'<span class="mx-badge mx-badge--{tone}">'
        f'<span class="mx-badge__dot" aria-hidden="true"></span>'
        f"{text}</span>"
    )


@register.inclusion_tag("website/partials/source_icon.html")
def source_icon(channel, size="md"):
    return {"channel": (channel or "").upper(), "size": size}
