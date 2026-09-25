"""
MoneXa User model — Custom User with RBAC roles.

Three roles (RBAC):
- CAISSIER  : terrain (saisie mobile, ses propres paiements)
- COMPTABLE : back-office (validation A_VALIDER, exports)
- GERANT    : autorité complète (anomalies, audit, users, 2FA)
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager


class Role(models.TextChoices):
    GERANT = "GERANT", "Gérant"
    COMPTABLE = "COMPTABLE", "Comptable"
    CAISSIER = "CAISSIER", "Caissier"


class Organization(models.Model):
    """Tenant SaaS — une entreprise, un espace de données isolé."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=80)
    sector = models.CharField(max_length=120, blank=True, default="")
    country = models.CharField(max_length=2, default="TG")
    currency = models.CharField(max_length=3, default="XOF")
    legal_id = models.CharField(max_length=80, blank=True, default="")
    onboarded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "organisation"
        verbose_name_plural = "organisations"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    # USERNAME_FIELD = email (username kept for Django Admin compatibility but
    # email is the real login identifier)
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True, db_index=True)

    # RBAC
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CAISSIER,
        db_index=True,
    )

    # Mobile Money phone (T-Money / Moov / Flooz)
    phone = models.CharField(max_length=20, blank=True, default="")

    # 2FA TOTP — optionnel pour le Gérant
    is_2fa_enabled = models.BooleanField(default=False)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="members",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["role"]

    objects = UserManager()

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return f"{self.email} ({self.get_role_display()})"

    # ── Helpers RBAC ────────────────────────────────────────────────────
    def is_gerant(self) -> bool:
        return self.role == Role.GERANT or self.is_superuser

    def is_comptable_or_higher(self) -> bool:
        return self.is_gerant() or self.role == Role.COMPTABLE

    def is_caissier_or_higher(self) -> bool:
        return self.is_comptable_or_higher() or self.role == Role.CAISSIER

    @property
    def display_name(self) -> str:
        if self.get_full_name():
            return self.get_full_name()
        return self.email
