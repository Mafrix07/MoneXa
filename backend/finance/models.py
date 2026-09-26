"""
MoneXa finance models.

RÈGLES D'OR FINANCIÈRES (cahier des charges §6.1) :
1. Pas de FloatField pour l'argent → DecimalField(14, 2)
2. Contrainte DB unique=True sur provider_ref (anti-doublon natif)
3. Toute écriture dans transaction.atomic()
"""
import secrets
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.utils import timezone as dj_timezone


# ──────────────────────────────────────────────────────────────────────────
# Choices
# ──────────────────────────────────────────────────────────────────────────
class Channel(models.TextChoices):
    TMONEY = "TMONEY", "T-Money"
    MOOV = "MOOV", "Moov Money"
    BANQUE = "BANQUE", "Banque"
    ESPECES = "ESPECES", "Espèces"


class InvoiceStatus(models.TextChoices):
    BROUILLON = "BROUILLON", "Brouillon"
    EMISE = "EMISE", "Émise"
    EN_ATTENTE = "EN_ATTENTE", "En attente"  # historique = émise
    PARTIELLEMENT_PAYEE = "PARTIELLEMENT_PAYEE", "Partiellement payée"
    PAYEE = "PAYEE", "Payée"
    EN_RETARD = "EN_RETARD", "En retard"
    ANOMALIE = "ANOMALIE", "Anomalie"
    ANNULEE = "ANNULEE", "Annulée"
    ANNULE = "ANNULE", "Annulé"  # historique
    RECONCILIE = "RECONCILIE", "Réconcilié"  # historique


class PaymentStatus(models.TextChoices):
    NON_RATTACHE = "NON_RATTACHE", "Non rattaché"
    A_VALIDER = "A_VALIDER", "À valider"
    RECONCILIE = "RECONCILIE", "Réconcilié"
    ANOMALIE = "ANOMALIE", "Anomalie"


class MatchMethod(models.TextChoices):
    AUTO_MXA = "AUTO_MXA", "Référence MONEXA"
    AUTO_REF = "AUTO_REF", "Référence facture / opérateur"
    AUTO_MONTANT = "AUTO_MONTANT", "Montant + 7 jours"
    FUZZY = "FUZZY", "Fuzzy nom/téléphone"
    MANUEL = "MANUEL", "Validation manuelle"
    IA = "IA", "IA"


class ExpenseCategory(models.TextChoices):
    LOYER = "LOYER", "Loyer"
    SALAIRES = "SALAIRES", "Salaires"
    FOURNISSEURS = "FOURNISSEURS", "Fournisseurs"
    TRANSPORT = "TRANSPORT", "Transport"
    FOURNITURES = "FOURNITURES", "Fournitures"
    AUTRE = "AUTRE", "Autre"


# ──────────────────────────────────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────────────────────────────────
class Account(models.Model):
    """Treasury account per channel (T-Money, Moov Money, Banque, Espèces)."""
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.PROTECT,
        related_name="treasury_accounts",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100, verbose_name="Nom")
    channel = models.CharField(
        max_length=20, choices=Channel.choices, db_index=True, verbose_name="Canal"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="accounts",
        verbose_name="Propriétaire",
    )
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Compte de trésorerie"
        verbose_name_plural = "Comptes de trésorerie"
        unique_together = [("organization", "name", "channel")]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_channel_display()})"


class Invoice(models.Model):
    """
    Invoice émise par la PME — référence auto-générée FACT-YYYY-XXXX.
    """
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.PROTECT,
        related_name="invoices",
        null=True,
        blank=True,
    )
    reference = models.CharField(max_length=20, db_index=True)
    monexa_ref = models.CharField(
        max_length=16,
        db_index=True,
        blank=True,
        default="",
        verbose_name="Référence de paiement MONEXA",
        help_text="Identifiant court MXA-XXXXXX, distinct de FACT-* et de la réf opérateur.",
    )
    client_name = models.CharField(max_length=200, verbose_name="Client")
    client_phone = models.CharField(max_length=20, blank=True, default="")
    amount = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Montant (FCFA)"
    )
    issue_date = models.DateField(verbose_name="Date d'émission")
    due_date = models.DateField(verbose_name="Date d'échéance")
    status = models.CharField(
        max_length=32,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.EMISE,
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="invoices_created",
    )
    pos_ticket_id = models.CharField(
        max_length=80,
        blank=True,
        default="",
        db_index=True,
        verbose_name="Ticket caisse",
        help_text="Identifiant externe du logiciel de caisse (idempotence POS).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ["-issue_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "reference"],
                name="uniq_invoice_ref_per_org",
            ),
            models.UniqueConstraint(
                fields=["organization", "monexa_ref"],
                name="uniq_invoice_mxa_per_org",
                condition=~models.Q(monexa_ref=""),
            ),
            models.UniqueConstraint(
                fields=["organization", "pos_ticket_id"],
                name="uniq_invoice_pos_ticket_per_org",
                condition=~models.Q(pos_ticket_id=""),
            ),
        ]
        indexes = [
            models.Index(fields=["status", "issue_date"]),
            models.Index(fields=["client_phone"]),
            models.Index(fields=["monexa_ref"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference} — {self.client_name} ({self.amount:,.2f} FCFA)"

    @classmethod
    def generate_reference(cls, organization=None) -> str:
        """Generate next invoice reference: FACT-YYYY-XXXX (scoped to org)."""
        from datetime import date
        year = date.today().year
        prefix = f"FACT-{year}-"
        qs = cls.objects.filter(reference__startswith=prefix)
        if organization is not None:
            qs = qs.filter(organization=organization)
        last = qs.order_by("-reference").first()
        if last:
            try:
                seq = int(last.reference.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    def generate_monexa_ref(cls, organization=None) -> str:
        """MXA-XXXXXX : non séquentiel, non devinable, lisible en SMS."""
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        for _ in range(32):
            body = "".join(secrets.choice(alphabet) for _ in range(6))
            ref = f"MXA-{body}"
            qs = cls.objects.filter(monexa_ref=ref)
            if organization is not None:
                qs = qs.filter(organization=organization)
            if not qs.exists():
                return ref
        raise RuntimeError("Impossible de générer une référence MONEXA unique.")

    OPEN_STATUSES = frozenset({
        "BROUILLON", "EMISE", "EN_ATTENTE", "PARTIELLEMENT_PAYEE", "EN_RETARD",
    })
    CLOSED_STATUSES = frozenset({"ANNULEE", "ANNULE"})

    def counted_payments(self):
        from finance.models import PaymentStatus
        return self.payments.filter(status=PaymentStatus.RECONCILIE)

    def amount_paid(self) -> Decimal:
        total = Decimal("0.00")
        for p in self.counted_payments():
            total += p.amount
        return total

    def amount_due(self) -> Decimal:
        due = self.amount - self.amount_paid()
        return due if due > 0 else Decimal("0.00")

    def is_overpaid(self) -> bool:
        return self.amount_paid() > self.amount

    def recompute_from_payments(self) -> None:
        """Met à jour statut facture selon les paiements RECONCILIE uniquement."""
        if self.status in self.CLOSED_STATUSES:
            return
        paid = self.amount_paid()
        today = dj_timezone.now().date()
        if paid > self.amount:
            self.status = InvoiceStatus.ANOMALIE
        elif paid == self.amount:
            self.status = InvoiceStatus.PAYEE
        elif paid > 0:
            self.status = InvoiceStatus.PARTIELLEMENT_PAYEE
        elif self.due_date and self.due_date < today:
            self.status = InvoiceStatus.EN_RETARD
        else:
            self.status = InvoiceStatus.EMISE
        self.save(update_fields=["status", "updated_at"])

    def save(self, *args, **kwargs):
        if not self.monexa_ref:
            self.monexa_ref = self.generate_monexa_ref(self.organization)
        super().save(*args, **kwargs)


class Payment(models.Model):
    """
    Payment reçu — entité centrale du pipeline IA.

    RÈGLES D'OR :
    - provider_ref unique=True (anti-doublon natif au niveau DB)
    - amount DecimalField(14, 2) — jamais de FloatField
    - paid_at indexé pour optimiser les requêtes dashboard
    """
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.PROTECT,
        related_name="payments",
        null=True,
        blank=True,
    )
    provider_ref = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Référence opérateur",
        help_text="Référence unique de la transaction Mobile Money (par organisation).",
    )
    amount = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Montant (FCFA)"
    )
    channel = models.CharField(
        max_length=20, choices=Channel.choices, db_index=True, verbose_name="Canal"
    )
    payer_name = models.CharField(max_length=200, blank=True, default="", verbose_name="Payeur")
    payer_phone = models.CharField(max_length=20, blank=True, default="", verbose_name="Téléphone payeur")
    paid_at = models.DateTimeField(db_index=True, verbose_name="Date de paiement")

    # Preuve et traçabilité IA
    evidence_image = models.ImageField(
        upload_to="evidence/%Y/%m/", blank=True, null=True, verbose_name="Image de preuve"
    )
    raw_text = models.TextField(
        blank=True, default="", verbose_name="Texte brut extrait par l'IA"
    )
    ai_confidence = models.FloatField(
        default=0.0, verbose_name="Score de confiance IA (0-1)"
    )

    # Réconciliation
    match_method = models.CharField(
        max_length=20, choices=MatchMethod.choices, default=MatchMethod.MANUEL,
        verbose_name="Méthode de matching",
    )
    status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.NON_RATTACHE,
        db_index=True, verbose_name="Statut",
    )
    invoice = models.ForeignKey(
        Invoice, on_delete=models.PROTECT, null=True, blank=True,
        related_name="payments", verbose_name="Facture rapprochée",
    )
    anomaly_score = models.FloatField(default=0.0, verbose_name="Score d'anomalie (0-1)")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="payments_created", verbose_name="Saisi par",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ["-paid_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "provider_ref"],
                name="uniq_payment_ref_per_org",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "paid_at"]),
            models.Index(fields=["channel", "paid_at"]),
            models.Index(fields=["anomaly_score"]),
        ]

    def __str__(self) -> str:
        return f"{self.provider_ref} — {self.amount:,.2f} FCFA ({self.get_channel_display()})"

    def clean(self):
        if self.amount <= Decimal("0"):
            raise ValidationError({"amount": "Le montant doit être strictement positif."})
        if not (0 <= self.ai_confidence <= 1):
            raise ValidationError({"ai_confidence": "Le score IA doit être entre 0 et 1."})


class Expense(models.Model):
    """Flux sortants — fournisseurs, salaires, loyer."""
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.PROTECT,
        related_name="expenses",
        null=True,
        blank=True,
    )
    supplier = models.CharField(max_length=200, verbose_name="Fournisseur / Bénéficiaire")
    category = models.CharField(
        max_length=20, choices=ExpenseCategory.choices,
        default=ExpenseCategory.AUTRE, verbose_name="Catégorie",
    )
    amount = models.DecimalField(
        max_digits=14, decimal_places=2, verbose_name="Montant (FCFA)"
    )
    paid_at = models.DateTimeField(db_index=True, verbose_name="Date de paiement")
    receipt_image = models.ImageField(
        upload_to="expenses/%Y/%m/", blank=True, null=True, verbose_name="Justificatif"
    )
    note = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="expenses_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"
        ordering = ["-paid_at"]

    def __str__(self) -> str:
        return f"{self.supplier} — {self.amount:,.2f} FCFA ({self.get_category_display()})"


class ConnectorKind(models.TextChoices):
    TMONEY = "TMONEY", "T-Money"
    MOOV = "MOOV", "Moov Money"
    BANQUE = "BANQUE", "Banque"
    ESPECES = "ESPECES", "Caisse"
    CSV = "CSV", "CSV / Excel"
    SMS = "SMS", "SMS"
    MANUAL = "MANUAL", "Saisie manuelle"


class IntegrationMethod(models.TextChoices):
    SIMULATED_API = "SIMULATED_API", "Connecteur simulé (aucune API opérateur réelle)"
    CSV = "CSV", "Import CSV / Excel"
    SMS = "SMS", "Preuve SMS"
    PHOTO = "PHOTO", "Photo / capture"
    MANUAL = "MANUAL", "Saisie manuelle"


class SourceStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Actif"
    IDLE = "IDLE", "En attente"
    ERROR = "ERROR", "Erreur"
    DISABLED = "DISABLED", "Désactivé"


class SyncStatus(models.TextChoices):
    RUNNING = "RUNNING", "En cours"
    SUCCESS = "SUCCESS", "Succès"
    PARTIAL = "PARTIAL", "Partiel"
    ERROR = "ERROR", "Erreur"


class FinancialSource(models.Model):
    """
    Source financière affichée dans « Sources ».

    Les connecteurs T-Money / Moov / banque sont SIMULÉS :
    aucune API opérateur n'est branchée. L'architecture permet de
    remplacer Simulated*Connector par une intégration réelle plus tard.
    """
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.PROTECT,
        related_name="financial_sources",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=120)
    connector_kind = models.CharField(max_length=20, choices=ConnectorKind.choices)
    integration_method = models.CharField(
        max_length=20,
        choices=IntegrationMethod.choices,
        default=IntegrationMethod.SIMULATED_API,
    )
    account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True, related_name="sources",
    )
    channel = models.CharField(max_length=20, choices=Channel.choices, db_index=True)
    is_simulated = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20, choices=SourceStatus.choices, default=SourceStatus.IDLE,
    )
    merchant_mask = models.CharField(max_length=32, blank=True, default="")
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_success_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True, default="")
    cursor = models.CharField(max_length=120, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="financial_sources",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Source financière"
        verbose_name_plural = "Sources financières"
        ordering = ["channel", "name"]

    def __str__(self) -> str:
        sim = "simulé" if self.is_simulated else "live"
        return f"{self.name} ({sim})"


class ConnectorSync(models.Model):
    """Journal d'une synchronisation de connecteur (idempotente)."""
    source = models.ForeignKey(
        FinancialSource, on_delete=models.CASCADE, related_name="syncs",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=SyncStatus.choices, default=SyncStatus.RUNNING,
    )
    created_count = models.PositiveIntegerField(default=0)
    ignored_count = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    cursor_before = models.CharField(max_length=120, blank=True, default="")
    cursor_after = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        verbose_name = "Synchronisation connecteur"
        verbose_name_plural = "Synchronisations connecteur"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.source_id} {self.status} +{self.created_count}/skip {self.ignored_count}"


class PosCredential(models.Model):
    """
    Jeton Bearer pour un logiciel de caisse.
    Le secret en clair n'est jamais stocké — uniquement un SHA-256.
    """
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.PROTECT,
        related_name="pos_credentials",
    )
    name = models.CharField(max_length=80, default="Caisse")
    channel = models.CharField(
        max_length=20, choices=Channel.choices, default=Channel.ESPECES,
    )
    token_hash = models.CharField(max_length=64, unique=True)
    token_hint = models.CharField(max_length=8, blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pos_credentials",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Jeton caisse"
        verbose_name_plural = "Jetons caisse"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        state = "révoqué" if self.revoked_at else "actif"
        return f"{self.name} …{self.token_hint} ({state})"

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


class ForecastCache(models.Model):
    """Cache des prévisions Holt-Winters (pré-calculées via generate_forecast)."""
    organization = models.ForeignKey(
        "accounts.Organization",
        on_delete=models.CASCADE,
        related_name="forecast_caches",
        null=True,
        blank=True,
    )
    days = models.PositiveSmallIntegerField(default=7)
    forecast_data = models.JSONField(default=list)
    confidence_low = models.JSONField(default=list)
    confidence_high = models.JSONField(default=list)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cache prévision"
        verbose_name_plural = "Caches prévisions"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "days"],
                name="uniq_forecast_days_per_org",
            ),
        ]

    def __str__(self) -> str:
        return f"Forecast J+{self.days} (généré {self.generated_at:%Y-%m-%d %H:%M})"
