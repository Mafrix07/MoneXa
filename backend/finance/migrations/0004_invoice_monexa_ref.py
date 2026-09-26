from django.db import migrations, models


def backfill_monexa_refs(apps, schema_editor):
    Invoice = apps.get_model("finance", "Invoice")
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    import secrets

    used = set(
        Invoice.objects.exclude(monexa_ref="").values_list("monexa_ref", flat=True)
    )
    for invoice in Invoice.objects.filter(monexa_ref=""):
        for _ in range(32):
            body = "".join(secrets.choice(alphabet) for _ in range(6))
            ref = f"MXA-{body}"
            if ref not in used:
                used.add(ref)
                invoice.monexa_ref = ref
                invoice.save(update_fields=["monexa_ref"])
                break


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0003_organization_tenancy"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="monexa_ref",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                help_text="Identifiant court MXA-XXXXXX, distinct de FACT-* et de la réf opérateur.",
                max_length=16,
                verbose_name="Référence de paiement MONEXA",
            ),
        ),
        migrations.AlterField(
            model_name="invoice",
            name="status",
            field=models.CharField(
                choices=[
                    ("BROUILLON", "Brouillon"),
                    ("EMISE", "Émise"),
                    ("EN_ATTENTE", "En attente"),
                    ("PARTIELLEMENT_PAYEE", "Partiellement payée"),
                    ("PAYEE", "Payée"),
                    ("EN_RETARD", "En retard"),
                    ("ANOMALIE", "Anomalie"),
                    ("ANNULEE", "Annulée"),
                    ("ANNULE", "Annulé"),
                    ("RECONCILIE", "Réconcilié"),
                ],
                db_index=True,
                default="EMISE",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="match_method",
            field=models.CharField(
                choices=[
                    ("AUTO_MXA", "Référence MONEXA"),
                    ("AUTO_REF", "Référence facture / opérateur"),
                    ("AUTO_MONTANT", "Montant + 7 jours"),
                    ("FUZZY", "Fuzzy nom/téléphone"),
                    ("MANUEL", "Validation manuelle"),
                    ("IA", "IA"),
                ],
                default="MANUEL",
                max_length=20,
                verbose_name="Méthode de matching",
            ),
        ),
        migrations.RunPython(backfill_monexa_refs, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.UniqueConstraint(
                condition=models.Q(("monexa_ref", ""), _negated=True),
                fields=("organization", "monexa_ref"),
                name="uniq_invoice_mxa_per_org",
            ),
        ),
        migrations.AddIndex(
            model_name="invoice",
            index=models.Index(fields=["monexa_ref"], name="finance_inv_monexa_idx"),
        ),
    ]
