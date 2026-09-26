"""
Management command: seed_demo

Judy's Spices — Lomé. Judy (gérante), Djamie (comptable), Laura (caissière).
Ledger d'épicerie d'épices : factures restaurants/hôtels, Mixx/Moov/espèces, dépenses.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --reset
"""
from datetime import datetime, timezone
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.bootstrap import DEMO_PASSWORD, demo_organization, ensure_demo_staff
from finance.models import (
    Account,
    Channel,
    ConnectorSync,
    Expense,
    ExpenseCategory,
    FinancialSource,
    ForecastCache,
    Invoice,
    InvoiceStatus,
    MatchMethod,
    Payment,
    PaymentStatus,
)
from finance.services.demo_sources import ensure_default_sources
from finance.services.forecast import forecast_cashflow


def _dt(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


class Command(BaseCommand):
    help = "Seed Judy's Spices (Lomé) : équipe Judy / Djamie / Laura + ledger épices."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Efface le ledger de Judy's Spices avant de recharger.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        org = demo_organization()
        if options.get("reset"):
            self.stdout.write(self.style.WARNING("[reset] ledger Judy's Spices..."))
            ConnectorSync.objects.filter(source__organization=org).delete()
            FinancialSource.objects.filter(organization=org).delete()
            Payment.objects.filter(organization=org).delete()
            Invoice.objects.filter(organization=org).delete()
            Expense.objects.filter(organization=org).delete()
            Account.objects.filter(organization=org).delete()
            ForecastCache.objects.filter(organization=org).delete()

        staff = ensure_demo_staff(org)
        gerant = staff["GERANT"]
        comptable = staff["COMPTABLE"]
        caissier = staff["CAISSIER"]
        self.stdout.write("  [ok] Judy, Djamie, Laura")

        for channel_code, label in Channel.choices:
            Account.objects.get_or_create(
                name=label,
                channel=channel_code,
                organization=org,
                defaults={"owner": gerant, "is_active": True},
            )

        invoices = {}

        def inv(ref, mxa, client, phone, amount, issue, due, status=InvoiceStatus.EMISE):
            obj, created = Invoice.objects.get_or_create(
                reference=ref,
                organization=org,
                defaults={
                    "monexa_ref": mxa,
                    "client_name": client,
                    "client_phone": phone,
                    "amount": Decimal(str(amount)),
                    "issue_date": issue,
                    "due_date": due,
                    "status": status,
                    "created_by": comptable,
                },
            )
            if not created:
                obj.monexa_ref = mxa
                obj.client_name = client
                obj.client_phone = phone
                obj.amount = Decimal(str(amount))
                obj.issue_date = issue
                obj.due_date = due
                obj.status = status
                obj.created_by = comptable
                obj.save()
            invoices[ref] = obj
            return obj

        # Clients B2B de Judy's Spices (Lomé)
        inv("FACT-2026-00801", "MXA-K2N8P4", "Hôtel 2 Février", "+228 22 21 00 11", 185000, datetime(2026, 9, 12).date(), datetime(2026, 9, 26).date())
        inv("FACT-2026-00802", "MXA-R7M3Q9", "Restaurant Le Mandingue", "+228 90 14 22 18", 72000, datetime(2026, 9, 13).date(), datetime(2026, 9, 27).date())
        inv("FACT-2026-00803", "MXA-T4B6H2", "Revendeuse Adawlato", "+228 91 55 08 40", 45000, datetime(2026, 9, 14).date(), datetime(2026, 9, 21).date())
        inv("FACT-2026-00804", "MXA-W9C2L8", "Hôtel Sarakawa", "+228 22 27 65 65", 240000, datetime(2026, 9, 15).date(), datetime(2026, 9, 30).date())
        inv("FACT-2026-00805", "MXA-P3F5N7", "Maquis Chez Fafa", "+228 92 33 10 21", 28000, datetime(2026, 9, 16).date(), datetime(2026, 9, 23).date())
        inv("FACT-2026-00806", "MXA-H8D1V6", "Cafétéria Univ. de Lomé", "+228 22 25 50 70", 96000, datetime(2026, 9, 17).date(), datetime(2026, 10, 1).date())
        inv("FACT-2026-00807", "MXA-J5K9A3", "Pâtisserie La Paix", "+228 90 77 12 44", 36000, datetime(2026, 9, 18).date(), datetime(2026, 9, 25).date())
        inv("FACT-2026-00808", "MXA-L2S4Y8", "Ets Kossi Restauration", "+228 91 20 18 33", 150000, datetime(2026, 9, 19).date(), datetime(2026, 10, 3).date())
        inv("FACT-2026-00809", "MXA-N6E8C1", "Pharmacie du Grand Marché", "+228 22 21 44 88", 18000, datetime(2026, 9, 20).date(), datetime(2026, 9, 27).date())
        inv("FACT-2026-00810", "MXA-Q1Z7B5", "Traiteur Amenvi", "+228 70 12 45 09", 125000, datetime(2026, 9, 21).date(), datetime(2026, 10, 5).date())
        inv("FACT-2026-00811", "MXA-S8W3M2", "Restaurant Côté Jardin", "+228 93 01 66 12", 54000, datetime(2026, 9, 22).date(), datetime(2026, 10, 6).date())
        inv("FACT-2026-00812", "MXA-V4H9T6", "Boulangerie Tokoin", "+228 90 41 23 87", 22000, datetime(2026, 9, 23).date(), datetime(2026, 9, 30).date())
        inv("FACT-2026-00813", "MXA-Y7P2D4", "Hôtel Ibis Lomé", "+228 22 23 65 00", 310000, datetime(2026, 9, 24).date(), datetime(2026, 10, 8).date())
        inv("FACT-2026-00814", "MXA-B3K8F9", "Snack Avenue de la Paix", "+228 92 08 19 55", 15000, datetime(2026, 9, 25).date(), datetime(2026, 10, 2).date())

        def pay(ref, amount, channel, payer, phone, paid_at, status, method, invoice_ref=None, raw=""):
            inv_obj = invoices.get(invoice_ref) if invoice_ref else None
            obj, created = Payment.objects.get_or_create(
                organization=org,
                provider_ref=ref,
                defaults={
                    "amount": Decimal(str(amount)),
                    "channel": channel,
                    "payer_name": payer,
                    "payer_phone": phone,
                    "paid_at": paid_at,
                    "raw_text": raw,
                    "ai_confidence": 0.94,
                    "match_method": method,
                    "status": status,
                    "invoice": inv_obj,
                    "created_by": caissier,
                    "anomaly_score": 0.08 if status != PaymentStatus.ANOMALIE else 0.72,
                },
            )
            if not created:
                obj.amount = Decimal(str(amount))
                obj.channel = channel
                obj.payer_name = payer
                obj.payer_phone = phone
                obj.paid_at = paid_at
                obj.raw_text = raw
                obj.match_method = method
                obj.status = status
                obj.invoice = inv_obj
                obj.created_by = caissier
                obj.anomaly_score = 0.08 if status != PaymentStatus.ANOMALIE else 0.72
                obj.save()
            if inv_obj and status == PaymentStatus.RECONCILIE:
                inv_obj.recompute_from_payments()
            return obj

        # Paiements rattachés MXA (réconciliés)
        pay("TXK2N8P401", 185000, Channel.TMONEY, "Hôtel 2 Février", "+228 22 21 00 11", _dt(2026, 9, 13, 9, 40), PaymentStatus.RECONCILIE, MatchMethod.AUTO_MXA, "FACT-2026-00801", "T-Money 185000 FCFA MXA-K2N8P4 ID TXK2N8P401")
        pay("MV7M3Q9002", 72000, Channel.MOOV, "Restaurant Le Mandingue", "+228 90 14 22 18", _dt(2026, 9, 14, 11, 15), PaymentStatus.RECONCILIE, MatchMethod.AUTO_MXA, "FACT-2026-00802", "Moov Money 72000 FCFA MXA-R7M3Q9 ID MV7M3Q9002")
        pay("TXR7ADA003", 45000, Channel.TMONEY, "Revendeuse Adawlato", "+228 91 55 08 40", _dt(2026, 9, 15, 16, 5), PaymentStatus.RECONCILIE, MatchMethod.AUTO_MXA, "FACT-2026-00803", "T-Money 45000 FCFA MXA-T4B6H2")
        pay("CSFAFA004", 28000, Channel.ESPECES, "Maquis Chez Fafa", "+228 92 33 10 21", _dt(2026, 9, 16, 18, 30), PaymentStatus.RECONCILIE, MatchMethod.MANUEL, "FACT-2026-00805", "Espèces caisse Judy's Spices")
        pay("TXPAIX005", 36000, Channel.TMONEY, "Pâtisserie La Paix", "+228 90 77 12 44", _dt(2026, 9, 19, 8, 50), PaymentStatus.RECONCILIE, MatchMethod.AUTO_MXA, "FACT-2026-00807", "T-Money 36000 FCFA MXA-J5K9A3")
        pay("MVPHARM006", 18000, Channel.MOOV, "Pharmacie du Grand Marché", "+228 22 21 44 88", _dt(2026, 9, 21, 12, 10), PaymentStatus.RECONCILIE, MatchMethod.AUTO_MXA, "FACT-2026-00809", "Moov 18000 FCFA MXA-N6E8C1")
        pay("TXTOKOIN007", 22000, Channel.TMONEY, "Boulangerie Tokoin", "+228 90 41 23 87", _dt(2026, 9, 24, 7, 45), PaymentStatus.RECONCILIE, MatchMethod.AUTO_MXA, "FACT-2026-00812", "T-Money 22000 FCFA MXA-V4H9T6")
        pay("TXSNACK008", 15000, Channel.TMONEY, "Snack Avenue de la Paix", "+228 92 08 19 55", _dt(2026, 9, 26, 10, 5), PaymentStatus.RECONCILIE, MatchMethod.AUTO_MXA, "FACT-2026-00814", "T-Money 15000 FCFA MXA-B3K8F9")

        # Acompte (partiel) Hôtel Sarakawa
        pay("TXSARA009", 120000, Channel.TMONEY, "Hôtel Sarakawa", "+228 22 27 65 65", _dt(2026, 9, 18, 14, 20), PaymentStatus.RECONCILIE, MatchMethod.AUTO_MXA, "FACT-2026-00804", "T-Money acompte 120000 FCFA MXA-W9C2L8")

        # File à valider (montant, pas MXA dans le SMS)
        pay("TXUNIV010", 96000, Channel.TMONEY, "Cafétéria Univ. de Lomé", "+228 22 25 50 70", _dt(2026, 9, 20, 13, 0), PaymentStatus.A_VALIDER, MatchMethod.AUTO_MONTANT, "FACT-2026-00806", "T-Money 96000 FCFA ID TXUNIV010")
        pay("MVRAMEN011", 125000, Channel.MOOV, "Traiteur Amenvi", "+228 70 12 45 09", _dt(2026, 9, 22, 17, 40), PaymentStatus.A_VALIDER, MatchMethod.AUTO_MONTANT, "FACT-2026-00810", "Moov 125000 FCFA ID MVRAMEN011")

        # Non rattaché
        pay("TXWALK012", 8500, Channel.TMONEY, "Client passage", "+228 90 00 61 22", _dt(2026, 9, 23, 11, 25), PaymentStatus.NON_RATTACHE, MatchMethod.MANUEL, None, "T-Money 8500 FCFA poivre sachet")
        pay("MVCASH013", 12000, Channel.MOOV, "Client non nommé", "+228 91 44 00 19", _dt(2026, 9, 25, 15, 55), PaymentStatus.NON_RATTACHE, MatchMethod.MANUEL, None, "Moov 12000 FCFA")

        # Anomalie : écart de montant vs facture jardin
        pay("TXJARD014", 60000, Channel.TMONEY, "Restaurant Côté Jardin", "+228 93 01 66 12", _dt(2026, 9, 23, 19, 10), PaymentStatus.ANOMALIE, MatchMethod.AUTO_REF, "FACT-2026-00811", "T-Money 60000 FCFA FACT-2026-00811 (facture 54000)")

        # Anomalie : paiement nocturne
        pay("TXNIGHT015", 41000, Channel.MOOV, "Inconnu", "+228 70 99 01 02", _dt(2026, 9, 21, 3, 12), PaymentStatus.ANOMALIE, MatchMethod.MANUEL, None, "Moov 41000 FCFA 03h12")

        # Espèces + banque pour les graphes canal
        pay("BQEPIC016", 200000, Channel.BANQUE, "Hôtel Ibis Lomé", "+228 22 23 65 00", _dt(2026, 9, 25, 9, 0), PaymentStatus.A_VALIDER, MatchMethod.AUTO_MONTANT, "FACT-2026-00813", "Virement 200000 FCFA Ibis")
        pay("CSKOS017", 75000, Channel.ESPECES, "Ets Kossi Restauration", "+228 91 20 18 33", _dt(2026, 9, 22, 16, 0), PaymentStatus.RECONCILIE, MatchMethod.MANUEL, "FACT-2026-00808", "Acompte espèces 75000 sur 150000")

        self.stdout.write("  [ok] Factures et paiements Judy's Spices")

        expenses = [
            ("Marché d'Adawlato", ExpenseCategory.FOURNISSEURS, 85000, _dt(2026, 9, 13, 7, 30), "Piment, gingembre, clou de girofle"),
            ("CEET Lomé", ExpenseCategory.AUTRE, 22000, _dt(2026, 9, 15, 10, 0), "Facture électricité kiosque"),
            ("ImmoLoc Grand Marché", ExpenseCategory.LOYER, 120000, _dt(2026, 9, 16, 9, 0), "Loyer stand Judy's Spices"),
            ("Sacs et sachets Tokoin", ExpenseCategory.FOURNITURES, 18000, _dt(2026, 9, 18, 11, 20), "Emballage condiments"),
            ("Taxi-moto stock", ExpenseCategory.TRANSPORT, 6000, _dt(2026, 9, 19, 8, 10), "Livraison Hôtel 2 Février"),
            ("Fournisseur Aného", ExpenseCategory.FOURNISSEURS, 64000, _dt(2026, 9, 22, 6, 45), "Sel, cubèbe, nora"),
            ("Laura — avance semaine", ExpenseCategory.SALAIRES, 35000, _dt(2026, 9, 24, 17, 0), "Avance caissière"),
            ("Togocom", ExpenseCategory.AUTRE, 5000, _dt(2026, 9, 25, 12, 0), "Crédit data caisse"),
        ]
        for supplier, cat, amount, when, note in expenses:
            Expense.objects.get_or_create(
                organization=org,
                supplier=supplier,
                paid_at=when,
                defaults={
                    "category": cat,
                    "amount": Decimal(str(amount)),
                    "note": note,
                    "created_by": comptable,
                },
            )
        self.stdout.write("  [ok] Dépenses")

        try:
            for days in (7, 30):
                f = forecast_cashflow(days=days, organization=org)
                ForecastCache.objects.update_or_create(
                    days=days,
                    organization=org,
                    defaults={
                        "forecast_data": f.get("forecast", []),
                        "confidence_low": f.get("confidence_low", []),
                        "confidence_high": f.get("confidence_high", []),
                    },
                )
            self.stdout.write("  [ok] Prévisions")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  [warn] Prévisions : {e}"))

        ensure_default_sources(gerant)
        self.stdout.write("  [ok] Sources simulées")

        self.stdout.write(self.style.SUCCESS("\nJudy's Spices — Lomé, Togo"))
        self.stdout.write(f"  Gérante    : judy@judyspices.tg / {DEMO_PASSWORD}  (Judy)")
        self.stdout.write(f"  Comptable  : djamie@judyspices.tg / {DEMO_PASSWORD}  (Djamie)")
        self.stdout.write(f"  Caissière  : laura@judyspices.tg / {DEMO_PASSWORD}  (Laura)")
        self.stdout.write("  Ensuite : python manage.py seed_golden_demo  (parcours jury MXA)")
