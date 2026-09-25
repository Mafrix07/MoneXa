"""Accounts signals — auto-log user creation to the audit chain."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User


@receiver(post_save, sender=User)
def _log_user_creation(sender, instance, created, **kwargs):
    if not created:
        return
    # Imported lazily to avoid an import cycle at app-loading time.
    from auditing.services import log_action

    try:
        log_action(
            user=instance,
            action="USER_CREATED",
            entity="User",
            entity_id=str(instance.pk),
            details={"email": instance.email, "role": instance.role},
        )
    except Exception:
        # Audit must never crash user creation.
        pass
