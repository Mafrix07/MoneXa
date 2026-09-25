"""
Signals — auto-log sensitive actions via AuditLog.

Connected in AuditingConfig.ready() to:
- Payment.post_save (created=True) → PAYMENT_CREATED
- Invoice.post_save (created=True) → INVOICE_CREATED
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User
from finance.models import Payment, Invoice

from .services import log_action


@receiver(post_save, sender=Payment)
def log_payment_created(sender, instance, created, **kwargs):
    if not created:
        return
    log_action(
        user=instance.created_by,
        action="PAYMENT_CREATED",
        entity="Payment",
        entity_id=instance.id,
        details={
            "provider_ref": instance.provider_ref,
            "amount": float(instance.amount),
            "channel": instance.channel,
            "status": instance.status,
            "match_method": instance.match_method,
            "ai_confidence": instance.ai_confidence,
            "invoice_id": instance.invoice_id,
        },
    )


@receiver(post_save, sender=Invoice)
def log_invoice_created(sender, instance, created, **kwargs):
    if not created:
        return
    log_action(
        user=instance.created_by,
        action="INVOICE_CREATED",
        entity="Invoice",
        entity_id=instance.id,
        details={
            "reference": instance.reference,
            "amount": float(instance.amount),
            "client_name": instance.client_name,
            "status": instance.status,
        },
    )
