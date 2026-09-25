"""Audit admin — read-only, no add/delete."""
from django.contrib import admin
from .models import AuditLog, BrokenChainEntry


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "timestamp", "user", "action", "entity", "entity_id", "hash_short")
    list_filter = ("action", "entity")
    search_fields = ("action", "entity_id", "user__email")
    date_hierarchy = "timestamp"
    ordering = ("-timestamp",)

    readonly_fields = [
        "user", "action", "entity", "entity_id", "details", "ip_address",
        "timestamp", "prev_hash", "hash",
    ]

    def hash_short(self, obj):
        return obj.hash[:16] + "…" if obj.hash else "—"
    hash_short.short_description = "Hash"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_gerant():
            return qs
        return qs.none()

    def has_module_permission(self, request):
        return request.user.is_authenticated and request.user.is_gerant()


@admin.register(BrokenChainEntry)
class BrokenChainEntryAdmin(admin.ModelAdmin):
    list_display = ("audit_log", "detected_at", "expected_hash", "actual_hash")
    readonly_fields = ("audit_log", "detected_at", "expected_hash", "actual_hash")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
