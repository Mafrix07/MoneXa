from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_organization_tenancy"),
        ("finance", "0004_invoice_monexa_ref"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="pos_ticket_id",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                help_text="Identifiant externe du logiciel de caisse (idempotence POS).",
                max_length=80,
                verbose_name="Ticket caisse",
            ),
        ),
        migrations.AddConstraint(
            model_name="invoice",
            constraint=models.UniqueConstraint(
                condition=models.Q(("pos_ticket_id", ""), _negated=True),
                fields=("organization", "pos_ticket_id"),
                name="uniq_invoice_pos_ticket_per_org",
            ),
        ),
        migrations.CreateModel(
            name="PosCredential",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="Caisse", max_length=80)),
                ("channel", models.CharField(choices=[("TMONEY", "T-Money"), ("MOOV", "Moov Money"), ("BANQUE", "Banque"), ("ESPECES", "Espèces")], default="ESPECES", max_length=20)),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("token_hint", models.CharField(blank=True, default="", max_length=8)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_used_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pos_credentials", to="accounts.user")),
                ("organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="pos_credentials", to="accounts.organization")),
            ],
            options={
                "verbose_name": "Jeton caisse",
                "verbose_name_plural": "Jetons caisse",
                "ordering": ["-created_at"],
            },
        ),
    ]
