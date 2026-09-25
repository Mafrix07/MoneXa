"""Finance serializers."""
from rest_framework import serializers
from .models import Account, Invoice, Payment, Expense, ForecastCache, Channel, InvoiceStatus, PaymentStatus


class AccountSerializer(serializers.ModelSerializer):
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)

    class Meta:
        model = Account
        fields = ["id", "name", "channel", "channel_display", "owner", "is_active", "created_at"]
        read_only_fields = ["id", "created_at", "owner"]


class InvoiceSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reference = serializers.CharField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "reference", "client_name", "client_phone", "amount",
            "issue_date", "due_date", "status", "status_display",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "reference", "created_by", "created_at", "updated_at"]


class PaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    match_method_display = serializers.CharField(source="get_match_method_display", read_only=True)
    invoice_reference = serializers.CharField(source="invoice.reference", read_only=True, default="")

    class Meta:
        model = Payment
        fields = [
            "id", "provider_ref", "amount", "channel", "channel_display",
            "payer_name", "payer_phone", "paid_at",
            "evidence_image", "raw_text", "ai_confidence",
            "match_method", "match_method_display",
            "status", "status_display",
            "invoice", "invoice_reference", "anomaly_score",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "ai_confidence", "match_method", "status", "invoice",
            "anomaly_score", "created_by", "created_at", "updated_at",
            "raw_text",
        ]


class ExpenseSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = Expense
        fields = [
            "id", "supplier", "category", "category_display", "amount",
            "paid_at", "receipt_image", "note", "created_by", "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]


class ForecastCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastCache
        fields = ["days", "forecast_data", "confidence_low", "confidence_high", "generated_at"]
