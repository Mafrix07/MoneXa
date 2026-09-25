"""Helpers d'organisation (seed / onboarding). Jamais appelé implicitement en production."""
from __future__ import annotations

from django.utils.text import slugify

from .models import Organization


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
    """Organisation de développement / démo uniquement."""
    return get_or_create_organization(
        name="Demo PME",
        slug="demo-pme",
        sector="Commerce",
        legal_id="DEV-ONLY",
    )
