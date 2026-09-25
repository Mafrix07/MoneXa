"""Audit serializers (read-only)."""
from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True, default="anonymous")
    user_role = serializers.CharField(source="user.role", read_only=True, default="")
    timestamp_iso = serializers.DateTimeField(source="timestamp", read_only=True)
    hash_short = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id", "user", "user_email", "user_role", "action", "entity", "entity_id",
            "details", "ip_address", "timestamp", "timestamp_iso",
            "prev_hash", "hash", "hash_short",
        ]
        read_only_fields = fields

    def get_hash_short(self, obj):
        return obj.hash[:16] + "…" if obj.hash else ""
