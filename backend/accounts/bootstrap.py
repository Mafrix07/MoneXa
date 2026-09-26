"""Helpers d'organisation (seed / onboarding). Jamais appelé implicitement en production."""
from __future__ import annotations

from django.utils.text import slugify

from .models import Organization, Role, User


def get_or_create_organization(*, name: str, slug: str | None = None, **extra) -> Organization:
    slug = slugify(slug or name)[:80] or "organisation"
    base = slug
    n = 1
    while Organization.objects.filter(slug=slug).exclude(name=name).exists():
        n += 1
        slug = f"{base}-{n}"[:80]
    org, _ = Organization.objects.get_or_create(
        slug=slug,
        defaults={"name": name, "country": "TG", "currency": "XOF", **extra},
    )
    return org


def demo_organization() -> Organization:
    """Judy's Spices — Lomé, Togo. Seed / démo uniquement."""
    org = get_or_create_organization(
        name="Judy's Spices",
        slug="judys-spices",
        sector="Épices et condiments",
        legal_id="Lomé, Togo",
        country="TG",
        currency="XOF",
    )
    dirty = False
    if org.name != "Judy's Spices":
        org.name = "Judy's Spices"
        dirty = True
    if org.sector != "Épices et condiments":
        org.sector = "Épices et condiments"
        dirty = True
    if org.legal_id != "Lomé, Togo":
        org.legal_id = "Lomé, Togo"
        dirty = True
    if org.country != "TG":
        org.country = "TG"
        dirty = True
    if dirty:
        org.save()
    return org


DEMO_PASSWORD = "Monexa2026!"

_STAFF = (
    {
        "email": "judy@judyspices.tg",
        "legacy": "gerant@monexa.tg",
        "role": Role.GERANT,
        "first_name": "Judy",
        "last_name": "",
        "phone": "+228 90 12 34 01",
        "is_staff": True,
        "is_2fa_enabled": True,
    },
    {
        "email": "djamie@judyspices.tg",
        "legacy": "comptable@monexa.tg",
        "role": Role.COMPTABLE,
        "first_name": "Djamie",
        "last_name": "",
        "phone": "+228 91 12 34 02",
        "is_staff": True,
        "is_2fa_enabled": False,
    },
    {
        "email": "laura@judyspices.tg",
        "legacy": "caissier@monexa.tg",
        "role": Role.CAISSIER,
        "first_name": "Laura",
        "last_name": "",
        "phone": "+228 92 12 34 03",
        "is_staff": False,
        "is_2fa_enabled": False,
    },
)


def ensure_demo_staff(org: Organization) -> dict[str, User]:
    """Judy (gérante), Djamie (comptable), Laura (caissière)."""
    people: dict[str, User] = {}
    for spec in _STAFF:
        user = User.objects.filter(email=spec["email"]).first()
        if user is None:
            legacy = User.objects.filter(email=spec["legacy"]).first()
            if legacy is not None:
                user = legacy
                user.email = spec["email"]
            else:
                user = User(email=spec["email"])
        user.role = spec["role"]
        user.first_name = spec["first_name"]
        user.last_name = spec["last_name"]
        user.phone = spec["phone"]
        user.is_staff = spec["is_staff"]
        user.is_2fa_enabled = spec["is_2fa_enabled"]
        user.organization = org
        user.set_password(DEMO_PASSWORD)
        user.save()
        people[spec["role"]] = user
    return people
