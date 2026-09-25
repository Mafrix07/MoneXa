"""Stamp organization from the creating user when missing."""
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Account, Expense, FinancialSource, Invoice, Payment


def _stamp(instance, user_attr: str) -> None:
    if instance.organization_id:
        return
    user = getattr(instance, user_attr, None)
    oid = getattr(user, "organization_id", None) if user else None
    if oid:
        instance.organization_id = oid


@receiver(pre_save, sender=Invoice)
def stamp_invoice_org(sender, instance, **kwargs):
    _stamp(instance, "created_by")


@receiver(pre_save, sender=Payment)
def stamp_payment_org(sender, instance, **kwargs):
    _stamp(instance, "created_by")


@receiver(pre_save, sender=Expense)
def stamp_expense_org(sender, instance, **kwargs):
    _stamp(instance, "created_by")


@receiver(pre_save, sender=Account)
def stamp_account_org(sender, instance, **kwargs):
    _stamp(instance, "owner")


@receiver(pre_save, sender=FinancialSource)
def stamp_source_org(sender, instance, **kwargs):
    _stamp(instance, "created_by")
