"""
Management command: anonymize_data

Anonymise les données réelles pour usage en démo.
Remplace les noms et téléphones réels par des données fictives.

Usage:
    python manage.py anonymize_data
"""
import random
from django.core.management.base import BaseCommand
from finance.models import Payment, Invoice, Expense

NAMES = ["Client Démo 1", "Client Démo 2", "Client Démo 3", "Client Démo 4"]
PHONES = ["+228 90 00 00 00", "+228 91 00 00 00", "+228 92 00 00 00"]


class Command(BaseCommand):
    help = "Anonymise les noms et téléphones réels dans les données (pour démo)."

    def handle(self, *args, **options):
        rng = random.Random(123)
        n_p = 0
        for p in Payment.objects.all():
            p.payer_name = rng.choice(NAMES)
            p.payer_phone = rng.choice(PHONES)
            p.save(update_fields=["payer_name", "payer_phone"])
            n_p += 1

        n_i = 0
        for i in Invoice.objects.all():
            i.client_name = rng.choice(NAMES)
            i.client_phone = rng.choice(PHONES)
            i.save(update_fields=["client_name", "client_phone"])
            n_i += 1

        n_e = 0
        for e in Expense.objects.all():
            e.supplier = f"Fournisseur Démo {rng.randint(1, 5)}"
            e.save(update_fields=["supplier"])
            n_e += 1

        self.stdout.write(self.style.SUCCESS(
            f"✅ Anonymisé: {n_p} paiements, {n_i} factures, {n_e} dépenses."
        ))
