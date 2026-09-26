"""
Scénario Golden Demo (reproductible).

1. Facture FACT-2026-00842 — MXA-8F42K7 — ABC SARL — 50 000 FCFA (EMISE)
2. L'utilisateur colle le SMS T-Money contenant MXA-8F42K7
3. Matcher AUTO_MXA → paiement RECONCILIE, facture PAYEE
4. Second import → 409 doublon (réf opérateur)

Usage:
    python manage.py seed_golden_demo
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from django.core.management.base import BaseCommand

from accounts.models import Role, User
from accounts.bootstrap import demo_organization
from finance.models import (
    Channel, Invoice, InvoiceStatus, MatchMethod, Payment, PaymentStatus,
)
from finance.services.demo_sources import ensure_default_sources

GOLDEN_SMS = (
    "T-Money: Vous avez recu 50000 FCFA de ABC SARL. "
    "Référence : MXA-8F42K7 ID TX8F42K700 le 25/09/2026 09:15"
)


class Command(BaseCommand):
    help = "Prépare le scénario de démo jury (facture ABC SARL 50 000 FCFA + MXA)."

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

        Payment.objects.filter(
            organization=org,
            provider_ref__in=["MV849321", "TX8F42K700", "TX92MEDIUM", "TXDUP-A", "TXDUP-B"],
        ).delete()

        inv, created = Invoice.objects.get_or_create(
            reference="FACT-2026-00842",
            organization=org,
            defaults={
                "monexa_ref": "MXA-8F42K7",
                "client_name": "ABC SARL",
                "client_phone": "+228 92 00 11 22",
                "amount": Decimal("50000"),
                "issue_date": date(2026, 9, 24),
                "due_date": date(2026, 10, 9),
                "status": InvoiceStatus.EMISE,
                "created_by": comptable,
            },
        )
        if not created:
            inv.monexa_ref = "MXA-8F42K7"
            inv.client_name = "ABC SARL"
            inv.amount = Decimal("50000")
            inv.status = InvoiceStatus.EMISE
            inv.issue_date = date(2026, 9, 24)
            inv.due_date = date(2026, 10, 9)
            inv.created_by = comptable
            inv.save()

        queued, _ = Invoice.objects.get_or_create(
            reference="FACT-2026-00850",
            organization=org,
            defaults={
                "client_name": "ABC SARL",
                "client_phone": "+228 92 00 11 22",
                "amount": Decimal("40000"),
                "issue_date": date(2026, 9, 24),
                "due_date": date(2026, 10, 9),
                "status": InvoiceStatus.EMISE,
                "created_by": comptable,
            },
        )
        if queued.amount != Decimal("40000"):
            queued.amount = Decimal("40000")
            queued.client_name = "ABC SARL"
            queued.status = InvoiceStatus.EMISE
            queued.save()

        paid_at = datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc)
        p92 = Payment.objects.create(
            organization=org,
            provider_ref="TX92MEDIUM",
            amount=Decimal("40000"),
            channel=Channel.TMONEY,
            payer_name="ABC SARL",
            paid_at=paid_at,
            raw_text="T-Money credit 40000 FCFA de ABC SARL ID TX92MEDIUM le 25/09/2026 10:00",
            created_by=caissier,
            status=PaymentStatus.A_VALIDER,
            match_method=MatchMethod.AUTO_MONTANT,
            invoice=queued,
        )

        Payment.objects.create(
            organization=org,
            provider_ref="TXDUP-A",
            amount=Decimal("12000"),
            channel=Channel.MOOV,
            payer_name="Payeur Demo",
            paid_at=paid_at,
            created_by=caissier,
            status=PaymentStatus.NON_RATTACHE,
        )
        Payment.objects.create(
            organization=org,
            provider_ref="TXDUP-B",
            amount=Decimal("12000"),
            channel=Channel.MOOV,
            payer_name="Payeur Demo",
            paid_at=paid_at + timedelta(minutes=8),
            created_by=caissier,
            status=PaymentStatus.ANOMALIE,
        )

        ensure_default_sources(gerant)
        self.stdout.write(self.style.SUCCESS("[ok] Golden demo pret"))
        self.stdout.write(f"  Facture : {inv.reference} / {inv.monexa_ref} / {inv.client_name} / {inv.amount} FCFA")
        self.stdout.write(f"  File A_VALIDER : {p92.provider_ref} ({queued.reference})")
        self.stdout.write(f"  Doublon potentiel : TXDUP-A / TXDUP-B")
        self.stdout.write("  SMS a coller :")
        self.stdout.write(f"  {GOLDEN_SMS}")
        self.stdout.write("  Connecteurs : SIMULES (aucune API operateur).")
