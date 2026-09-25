"""Isolation multi-tenant. Le backend refuse tout objet hors organisation."""
from __future__ import annotations


def organization_of(user):
    return getattr(user, "organization", None)


def organization_id_of(user) -> int | None:
    return getattr(user, "organization_id", None)


def filter_queryset_by_org(queryset, user, field: str = "organization"):
    if not user or not user.is_authenticated:
        return queryset.none()
    oid = organization_id_of(user)
    if oid is None:
        if getattr(user, "is_superuser", False):
            return queryset
        return queryset.none()
    return queryset.filter(**{field: oid})
