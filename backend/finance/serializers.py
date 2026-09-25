"""Finance serializers."""
from rest_framework import serializers
from .models import (
    Account, Invoice, Payment, Expense, ForecastCache,
    FinancialSource, ConnectorSync,
)


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

    def create(self, validated_data):
        validated_data["reference"] = Invoice.generate_reference()
        return super().create(validated_data)


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


class FinancialSourceSerializer(serializers.ModelSerializer):
    connector_kind_display = serializers.CharField(source="get_connector_kind_display", read_only=True)
    integration_method_display = serializers.CharField(
        source="get_integration_method_display", read_only=True,
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    transaction_count = serializers.SerializerMethodField()

    class Meta:
        model = FinancialSource
        fields = [
            "id", "name", "connector_kind", "connector_kind_display",
            "integration_method", "integration_method_display",
            "account", "channel", "is_simulated", "status", "status_display",
            "merchant_mask", "last_sync_at", "last_success_at", "last_error",
            "cursor", "is_active", "transaction_count", "created_at",
        ]
        read_only_fields = [
            "id", "last_sync_at", "last_success_at", "last_error", "cursor",
            "created_at", "is_simulated",
        ]

    def get_transaction_count(self, obj):
        return Payment.objects.filter(channel=obj.channel).count()


class ConnectorSyncSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectorSync
        fields = [
            "id", "source", "started_at", "finished_at", "status",
            "created_count", "ignored_count", "error_message",
            "cursor_before", "cursor_after",
        ]
        read_only_fields = fields


class ForecastCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForecastCache
        fields = ["days", "forecast_data", "confidence_low", "confidence_high", "generated_at"]
