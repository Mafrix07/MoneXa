"""Django Admin customization for accounts."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Role


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("email", "role", "phone", "is_2fa_enabled", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "phone", "username")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informations personnelles", {"fields": ("username", "phone", "role")}),
        ("Permissions", {
            "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions"),
        }),
        ("Sécurité 2FA", {"fields": ("is_2fa_enabled",)}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "role", "phone", "password1", "password2"),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Gérant voit tout ; Comptable en lecture seule ; Caissier rien
        if request.user.is_gerant():
            return qs
        if request.user.is_comptable_or_higher():
            return qs  # lecture via has_view_permission
        return qs.none()

    def has_module_permission(self, request):
        return request.user.is_authenticated and request.user.is_comptable_or_higher()

    def has_view_permission(self, request, obj=None):
        return request.user.is_comptable_or_higher()

    def has_change_permission(self, request, obj=None):
        return request.user.is_gerant()

    def has_delete_permission(self, request, obj=None):
        return request.user.is_gerant()

    def has_add_permission(self, request):
        return request.user.is_gerant()
