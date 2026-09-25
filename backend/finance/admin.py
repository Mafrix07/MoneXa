"""Finance admin customization."""
from django.contrib import admin
from django.utils.html import format_html
from .models import Account, Invoice, Payment, Expense, ForecastCache, FinancialSource, ConnectorSync


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "channel", "owner", "is_active", "created_at")
    list_filter = ("channel", "is_active")
    search_fields = ("name", "owner__email")
    ordering = ("channel", "name")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("reference", "client_name", "amount", "issue_date", "due_date", "status")
    list_filter = ("status", "issue_date")
    search_fields = ("reference", "client_name", "client_phone")
    date_hierarchy = "issue_date"
    ordering = ("-issue_date",)
    actions = ["marquer_validee", "marquer_anomalie"]

    @admin.action(description="✓ Marquer comme réconciliée")
    def marquer_validee(self, request, queryset):
        queryset.update(status="RECONCILIE")

    @admin.action(description="⚠ Marquer comme anomalie")
    def marquer_anomalie(self, request, queryset):
        queryset.update(status="ANOMALIE")

    def has_change_permission(self, request, obj=None):
        return request.user.is_comptable_or_higher()

    def has_add_permission(self, request):
        return request.user.is_caissier_or_higher()

    def has_delete_permission(self, request, obj=None):
        return request.user.is_gerant()


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "provider_ref", "amount", "channel_colored", "payer_name",
        "paid_at", "status_colored", "ai_confidence", "invoice_link",
    )
    list_filter = ("status", "channel", "match_method")
    search_fields = ("provider_ref", "payer_name", "payer_phone")
    date_hierarchy = "paid_at"
    ordering = ("-paid_at",)
    readonly_fields = ("raw_text", "ai_confidence", "anomaly_score", "created_at", "updated_at")
    actions = ["marquer_reconcilie", "marquer_anomalie"]

    def channel_colored(self, obj):
        colors = {
            "TMONEY": "#063082", "MOOV": "#059669", "FLOOZ": "#F59E0B",
            "BANQUE": "#9DA9C3", "ESPECES": "#6B7280",
        }
        color = colors.get(obj.channel, "#1A2539")
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:4px; font-size:11px;">{}</span>',
            color, obj.get_channel_display(),
        )
    channel_colored.short_description = "Canal"

    def status_colored(self, obj):
        colors = {
            "RECONCILIE": "#059669", "A_VALIDER": "#F59E0B",
            "ANOMALIE": "#DC2626", "NON_RATTACHE": "#6B7280",
        }
        color = colors.get(obj.status, "#1A2539")
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:4px; font-size:11px;">{}</span>',
            color, obj.get_status_display(),
        )
    status_colored.short_description = "Statut"

    def invoice_link(self, obj):
        if obj.invoice:
            return obj.invoice.reference
        return "—"
    invoice_link.short_description = "Facture"

    @admin.action(description="✓ Marquer comme réconcilié")
    def marquer_reconcilie(self, request, queryset):
        queryset.update(status="RECONCILIE")

    @admin.action(description="⚠ Marquer comme anomalie")
    def marquer_anomalie(self, request, queryset):
        queryset.update(status="ANOMALIE")

    def has_change_permission(self, request, obj=None):
        return request.user.is_comptable_or_higher()

    def has_delete_permission(self, request, obj=None):
        return request.user.is_gerant()


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("supplier", "category", "amount", "paid_at", "created_by")
    list_filter = ("category", "paid_at")
    search_fields = ("supplier",)
    date_hierarchy = "paid_at"
    ordering = ("-paid_at",)


@admin.register(ForecastCache)
class ForecastCacheAdmin(admin.ModelAdmin):
    list_display = ("days", "generated_at")
    readonly_fields = ("days", "forecast_data", "confidence_low", "confidence_high", "generated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_gerant()


@admin.register(FinancialSource)
class FinancialSourceAdmin(admin.ModelAdmin):
    list_display = (
        "name", "connector_kind", "channel", "is_simulated", "status",
        "last_sync_at", "merchant_mask",
    )
    list_filter = ("connector_kind", "is_simulated", "status")
    readonly_fields = ("last_sync_at", "last_success_at", "last_error", "cursor")


@admin.register(ConnectorSync)
class ConnectorSyncAdmin(admin.ModelAdmin):
    list_display = ("source", "status", "created_count", "ignored_count", "started_at")
    readonly_fields = (
        "source", "started_at", "finished_at", "status",
        "created_count", "ignored_count", "error_message",
        "cursor_before", "cursor_after",
    )

    def has_add_permission(self, request):
        return False


# Customise Admin site header
admin.site.site_header = "MoneXa — Back-office"
admin.site.site_title = "MoneXa Admin"
admin.site.index_title = "Tableau de bord"
