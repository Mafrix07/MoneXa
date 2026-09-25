"""Finance signals — auto-log Invoice/Payment creation to the audit chain."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from finance.models import Invoice, Payment


@receiver(post_save, sender=Invoice)
def _log_invoice_created(sender, instance, created, **kwargs):
    if not created:
        return
    from auditing.services import log_action
    try:
        log_action(
            user=instance.created_by,
            action="INVOICE_CREATED",
            entity="Invoice",
            entity_id=str(instance.pk),
            details={
                "reference": instance.reference,
                "client": instance.client_name,
                "amount": str(instance.amount),
                "status": instance.status,
            },
        )
    except Exception:
        pass


@receiver(post_save, sender=Payment)
def _log_payment_created(sender, instance, created, **kwargs):
    if not created:
        return
    from auditing.services import log_action
    try:
        log_action(
            user=instance.created_by,
            action="PAYMENT_CREATED",
            entity="Payment",
            entity_id=str(instance.pk),
            details={
                "provider_ref": instance.provider_ref,
                "amount": str(instance.amount),
                "channel": instance.channel,
                "status": instance.status,
                "match_method": instance.match_method,
            },
        )
    except Exception:
        pass
