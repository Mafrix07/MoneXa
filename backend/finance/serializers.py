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
    monexa_ref = serializers.CharField(read_only=True)
    amount_paid = serializers.SerializerMethodField()
    amount_due = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id", "reference", "monexa_ref", "client_name", "client_phone", "amount",
            "amount_paid", "amount_due",
            "issue_date", "due_date", "status", "status_display",
            "created_by", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "reference", "monexa_ref", "amount_paid", "amount_due",
            "created_by", "created_at", "updated_at",
        ]

    def get_amount_paid(self, obj):
        return str(obj.amount_paid())

    def get_amount_due(self, obj):
        return str(obj.amount_due())

    def create(self, validated_data):
        from auditing.services import log_action

        org = validated_data.get("organization")
        validated_data["reference"] = Invoice.generate_reference(organization=org)
        if not validated_data.get("monexa_ref"):
            validated_data["monexa_ref"] = Invoice.generate_monexa_ref(organization=org)
        invoice = super().create(validated_data)
        log_action(
            user=invoice.created_by,
            action="REFERENCE_GENEREE",
            entity="Invoice",
            entity_id=invoice.id,
            details={
                "reference": invoice.reference,
                "monexa_ref": invoice.monexa_ref,
            },
        )
        return invoice


class PaymentSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    match_method_display = serializers.CharField(source="get_match_method_display", read_only=True)
    invoice_reference = serializers.CharField(source="invoice.reference", read_only=True, default="")
    invoice_monexa_ref = serializers.CharField(source="invoice.monexa_ref", read_only=True, default="")

    class Meta:
        model = Payment
        fields = [
            "id", "provider_ref", "amount", "channel", "channel_display",
            "payer_name", "payer_phone", "paid_at",
            "evidence_image", "raw_text", "ai_confidence",
            "match_method", "match_method_display",
            "status", "status_display",
            "invoice", "invoice_reference", "invoice_monexa_ref", "anomaly_score",
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
