"""
RBAC permissions — role-based access control for MoneXa API.

Hierarchy: GERANT > COMPTABLE > CAISSIER
- CAISSIER  : can create invoices, upload payments, see own payments only
- COMPTABLE : can validate A_VALIDER, see all payments, export reports, Admin read
- GERANT    : can resolve anomalies, see audit logs, manage users, full Admin + 2FA
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Role


class IsCaissierOrHigher(BasePermission):
    """Any authenticated user with role CAISSIER, COMPTABLE or GERANT."""
    message = "Accès réservé aux utilisateurs authentifiés (Caissier minimum)."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_caissier_or_higher()


class IsComptableOrHigher(BasePermission):
    """COMPTABLE or GERANT only."""
    message = "Accès réservé au Comptable ou au Gérant."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_comptable_or_higher()


class IsGerant(BasePermission):
    """GERANT only."""
    message = "Accès réservé au Gérant."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_gerant()


class IsGerantOrReadOnly(BasePermission):
    """GERANT can write; COMPTABLE can read; CAISSIER denied."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return request.user.is_comptable_or_higher()
        return request.user.is_gerant()


class IsOwnerOrComptableOrHigher(BasePermission):
    """
    Used for Payment / Invoice retrieval:
    - CAISSIER sees only objects they created
    - COMPTABLE / GERANT see all
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_comptable_or_higher():
            return True
        # CAISSIER : only own objects
        created_by = getattr(obj, "created_by", None)
        return created_by == request.user
