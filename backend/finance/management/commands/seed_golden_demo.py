"""
Scénario Golden Demo (reproductible).

1. Facture FACT-2026-0001 — ABC Services — 50 000 FCFA
2. L'utilisateur importe le SMS Moov MV849321 (via /api/evidence/ kind=sms)
3. Matcher auto (montant + client + date)
4. Second import → 409 doublon potentiel

Usage:
    python manage.py seed_golden_demo
"""
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Role, User
from accounts.bootstrap import demo_organization
from finance.models import Invoice, InvoiceStatus, Payment
from finance.services.demo_sources import ensure_default_sources

GOLDEN_SMS = (
    "Moov Money: credit 50000 FCFA de ABC Services "
    "ID MV849321 le 25/09/2026 09:15"
)


class Command(BaseCommand):
    help = "Prépare le scénario de démo jury (facture ABC Services 50 000 FCFA)."

    def handle(self, *args, **options):
        org = demo_organization()
        gerant, _ = User.objects.get_or_create(
            email="gerant@monexa.tg",
            defaults={"role": Role.GERANT, "is_staff": True, "organization": org},
        )
        gerant.organization = org
        gerant.set_password("Monexa2026!")
        gerant.save()
        caissier, _ = User.objects.get_or_create(
            email="caissier@monexa.tg",
            defaults={"role": Role.CAISSIER, "organization": org},
        )
        caissier.organization = org
        caissier.set_password("Monexa2026!")
        caissier.save()
        comptable, _ = User.objects.get_or_create(
            email="comptable@monexa.tg",
            defaults={"role": Role.COMPTABLE, "is_staff": True, "organization": org},
        )
        comptable.organization = org
        comptable.set_password("Monexa2026!")
        comptable.save()

        Payment.objects.filter(provider_ref="MV849321", organization=org).delete()

        today = date(2026, 9, 25)
        inv, created = Invoice.objects.get_or_create(
            reference="FACT-2026-0001",
            organization=org,
            defaults={
                "client_name": "ABC Services",
                "client_phone": "+228 92 00 11 22",
                "amount": Decimal("50000"),
                "issue_date": date(2026, 9, 24),
                "due_date": date(2026, 10, 9),
                "status": InvoiceStatus.EN_ATTENTE,
                "created_by": caissier,
            },
        )
        if not created:
            inv.organization = org
            inv.client_name = "ABC Services"
            inv.amount = Decimal("50000")
            inv.status = InvoiceStatus.EN_ATTENTE
            inv.issue_date = date(2026, 9, 24)
            inv.due_date = date(2026, 10, 9)
            inv.save()

        ensure_default_sources(gerant)
        self.stdout.write(self.style.SUCCESS("[ok] Golden demo pret"))
        self.stdout.write(f"  Facture : {inv.reference} / {inv.client_name} / {inv.amount} FCFA")
        self.stdout.write("  SMS a coller :")
        self.stdout.write(f"  {GOLDEN_SMS}")
        self.stdout.write("  Connecteurs : SIMULES (aucune API operateur).")
