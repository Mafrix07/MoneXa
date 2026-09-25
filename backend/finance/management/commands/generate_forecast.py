"""
Management command: generate_forecast

Pré-calcul les prévisions Holt-Winters à J+7 et J+30 et les cache en base.
Optimise les performances du dashboard.

Usage:
    python manage.py generate_forecast
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from finance.models import ForecastCache
from finance.services.forecast import forecast_cashflow


class Command(BaseCommand):
    help = "Pré-calcule les prévisions Holt-Winters (J+7 et J+30) et les cache en base."

    @transaction.atomic
    def handle(self, *args, **options):
        for days in (7, 30):
            self.stdout.write(f"  ⏳ Calcul Holt-Winters J+{days}...")
            forecast = forecast_cashflow(days=days)

            ForecastCache.objects.update_or_create(
                days=days,
                defaults={
                    "forecast_data": forecast.get("forecast", []),
                    "confidence_low": forecast.get("confidence_low", []),
                    "confidence_high": forecast.get("confidence_high", []),
                },
            )
            self.stdout.write(
                f"  ✓ J+{days} — cumul prévu: "
                f"{forecast.get('cumulative_forecast', 0):,.0f} FCFA "
                f"(modèle: {forecast.get('model', 'n/a')})"
            )

        self.stdout.write(self.style.SUCCESS("\n✅ Prévisions générées et cachées."))
