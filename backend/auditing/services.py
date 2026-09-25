"""
AuditLog services — log_action + verify_chain.
"""
from __future__ import annotations
import logging
from typing import Optional
from django.db import transaction
from django.utils import timezone

from .models import AuditLog, BrokenChainEntry

logger = logging.getLogger("monexa.audit")


def log_action(
    *,
    user=None,
    action: str,
    entity: str,
    entity_id: str = "",
    details: Optional[dict] = None,
    ip_address: str | None = None,
) -> AuditLog:
    """
    Create an immutable audit entry. Computed prev_hash + hash chain.

    Args:
        user: User instance or None
        action: e.g. "PAYMENT_CREATED", "INVOICE_VALIDATED"
        entity: model name e.g. "Payment"
        entity_id: str representation of the entity PK
        details: optional dict with structured data
        ip_address: optional client IP

    Returns:
        The created AuditLog instance.
    """
    details = details or {}
    with transaction.atomic():
        entry = AuditLog(
            user=user,
            organization=getattr(user, "organization", None) if user else None,
            action=action,
            entity=entity,
            entity_id=str(entity_id or ""),
            details=details,
            ip_address=ip_address,
            timestamp=timezone.now(),
        )
        # save() will compute prev_hash + hash automatically
        entry.save()
    logger.info(f"AuditLog #{entry.id}: {action} {entity}:{entity_id} by {user or 'anonymous'}")
    return entry


def verify_chain() -> tuple[bool, list[dict]]:
    """
    Walk the audit chain from oldest to newest, recompute hashes, detect breaks.

    Returns:
        (is_intact, list_of_broken_entries)
        - is_intact: True if no breaks detected
        - list_of_broken_entries: [{"audit_log_id": ..., "expected_hash": ..., "actual_hash": ...}]
    """
    entries = list(AuditLog.objects.order_by("id"))
    broken: list[dict] = []
    expected_prev = "0" * 64

    for entry in entries:
        # Check prev_hash continuity
        if entry.prev_hash != expected_prev:
            broken.append({
                "audit_log_id": entry.id,
                "type": "prev_hash_mismatch",
                "expected_prev_hash": expected_prev,
                "actual_prev_hash": entry.prev_hash,
            })

        # Recompute hash
        recomputed = entry.compute_hash()
        if recomputed != entry.hash:
            broken.append({
                "audit_log_id": entry.id,
                "type": "hash_mismatch",
                "expected_hash": recomputed,
                "actual_hash": entry.hash,
            })

        expected_prev = entry.hash

    return (len(broken) == 0, broken)
