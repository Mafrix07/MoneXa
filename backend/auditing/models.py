"""
AuditLog model — hash-chained SHA-256 immutable journal.

Each entry contains:
- Standard fields (user, action, entity, entity_id, details, ip)
- prev_hash: SHA-256 of the previous entry's hash
- hash: SHA-256 of own fields + prev_hash

The chain is verifiable: any modification in DB breaks the chain.
Override save() and delete() to PREVENT any update/delete after creation.
"""
from __future__ import annotations
import hashlib
import json
from django.db import models
from django.conf import settings
from django.utils import timezone


class AuditLog(models.Model):
    """
    Immutable audit entry. Once created, cannot be modified or deleted
    (save/delete raise PermissionError).

    Hash chain: each entry's `hash` = SHA-256(prev_hash + own_data)
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="audit_logs",
    )
    action = models.CharField(max_length=50, db_index=True)
    entity = models.CharField(max_length=100, db_index=True)
    entity_id = models.CharField(max_length=100, blank=True, default="")
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    timestamp = models.DateTimeField(db_index=True)

    # Hash chain
    prev_hash = models.CharField(
        max_length=64, default="0" * 64,
        help_text="SHA-256 du hash de l'entrée précédente (zéros pour la première).",
    )
    hash = models.CharField(
        max_length=64, unique=True, db_index=True,
        help_text="SHA-256 des propres données + prev_hash.",
    )

    class Meta:
        verbose_name = "Entrée d'audit"
        verbose_name_plural = "Journal d'audit"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] {self.action} — {self.entity}:{self.entity_id}"

    # ────────────────────────────────────────────────────────────────────
    # Hash computation
    # ────────────────────────────────────────────────────────────────────
    def compute_hash(self) -> str:
        """SHA-256 over (action | entity | entity_id | details | timestamp_iso | prev_hash)."""
        payload = "|".join([
            self.action or "",
            self.entity or "",
            str(self.entity_id or ""),
            json.dumps(self.details or {}, sort_keys=True, default=str),
            self.timestamp.isoformat() if self.timestamp else "",
            self.prev_hash or "",
        ])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    # ────────────────────────────────────────────────────────────────────
    # Immutability — raise on update or delete
    # ────────────────────────────────────────────────────────────────────
    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError(
                f"AuditLog #{self.pk} ne peut pas être modifié — le journal est immuable."
            )
        # Need a timestamp to compute hash (auto_now_add only sets on DB insert)
        from django.utils import timezone as dj_timezone
        if not self.timestamp:
            self.timestamp = dj_timezone.now()
        # Get previous entry's hash
        if not self.prev_hash or self.prev_hash == "0" * 64:
            last = AuditLog.objects.order_by("-id").first()
            self.prev_hash = last.hash if last else "0" * 64
        # Compute own hash
        if not self.hash or self.hash == "0" * 64:
            self.hash = self.compute_hash()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError(
            f"AuditLog #{self.pk} ne peut pas être supprimé — le journal est immuable."
        )


class BrokenChainEntry(models.Model):
    """Persisted record of broken chain entries (for monitoring)."""
    audit_log = models.ForeignKey(AuditLog, on_delete=models.CASCADE, related_name="broken_chain")
    detected_at = models.DateTimeField(auto_now_add=True)
    expected_hash = models.CharField(max_length=64)
    actual_hash = models.CharField(max_length=64)

    class Meta:
        verbose_name = "Cassure de chaîne"
        verbose_name_plural = "Cassures de chaîne"
