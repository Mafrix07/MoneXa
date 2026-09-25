from django.apps import AppConfig


class AuditingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "auditing"
    verbose_name = "Journal d'audit immuable"

    def ready(self):
        # Connect signals
        from . import signals  # noqa: F401
