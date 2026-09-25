"""
Prévisions de trésorerie — Holt-Winters (lissage exponentiel triple).

Cahier des charges §13.1:
- Méthode : ExponentialSmoothing (statsmodels) avec tendance + saisonnalité
- Données : 90 jours d'historique de flux nets (encaissements - décaissements)
- Sortie : prévisions à J+7 et J+30 avec intervalle de confiance à 80%
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional
import logging

from finance.models import Payment, Expense

logger = logging.getLogger("monexa.forecast")

# Holt-Winters parameters
SEASONAL_PERIODS = 7  # weekly seasonality
FORECAST_DAYS = (7, 30)
CONFIDENCE_LEVEL = 0.80


def _collect_net_flux(days: int = 90) -> List[dict]:
    """
    Collect daily net flux (encaissements - décaissements) for the last N days.

    Returns:
        [{"date": "2026-09-01", "net": 125000.0}, ...]
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    flux = []
    for i in range(days):
        day = (start + timedelta(days=i)).date()
        next_day = day + timedelta(days=1)

        encashed = Decimal("0")
        for p in Payment.objects.filter(paid_at__date=day):
            encashed += p.amount

        spent = Decimal("0")
        for e in Expense.objects.filter(paid_at__date__gte=day, paid_at__date__lt=next_day):
            spent += e.amount

        flux.append({
            "date": day.isoformat(),
            "net": float(encashed - spent),
        })
    return flux


def forecast_cashflow(days: int = 30) -> dict:
    """
    Holt-Winters forecast for the next N days.

    Returns:
        {
            "days": 30,
            "historical": [flux for last 90 days],
            "forecast": [predicted net flux for next N days],
            "confidence_low": [low bound 80% CI],
            "confidence_high": [high bound 80% CI],
            "cumulative_forecast": float,
            "model": "Holt-Winters (triple exponential smoothing)",
        }
    """
    historical = _collect_net_flux(days=90)
    series = [h["net"] for h in historical]

    if len(series) < 14:
        # Fallback: simple moving average if not enough data
        avg = sum(series) / max(len(series), 1) if series else 0.0
        forecast = [avg for _ in range(days)]
        std_dev = (sum((x - avg) ** 2 for x in series) / max(len(series), 1)) ** 0.5
        conf_low = [f - 1.28 * std_dev for f in forecast]
        conf_high = [f + 1.28 * std_dev for f in forecast]
        return {
            "days": days,
            "historical": historical,
            "forecast": forecast,
            "confidence_low": conf_low,
            "confidence_high": conf_high,
            "cumulative_forecast": sum(forecast),
            "model": "Moving average fallback (insufficient data for Holt-Winters)",
        }

    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        import numpy as np

        ts = np.array(series, dtype=float)

        # Try Holt-Winters with additive trend + weekly seasonality
        # If seasonal_periods too large for the data, fall back to simple exponential
        try:
            model = ExponentialSmoothing(
                ts,
                trend="add",
                seasonal="add" if len(ts) >= 2 * SEASONAL_PERIODS else None,
                seasonal_periods=SEASONAL_PERIODS,
                initialization_method="estimated",
            )
            fitted = model.fit()
            forecast_arr = fitted.forecast(steps=days)
            forecast = forecast_arr.tolist()

            # Confidence interval via residual std
            residuals = ts - fitted.fittedvalues
            std_dev = float(residuals.std()) if len(residuals) > 1 else 1000.0
            z = 1.28  # ~80% two-sided
            conf_low = [f - z * std_dev for f in forecast]
            conf_high = [f + z * std_dev for f in forecast]

            model_name = "Holt-Winters (triple exponential smoothing, additive)"
        except Exception as e:
            logger.warning(f"Holt-Winters failed, falling back: {e}")
            # Fallback: simple exponential smoothing
            alpha = 0.3
            level = series[-1]
            forecast = [level for _ in range(days)]
            std_dev = (sum((x - level) ** 2 for x in series) / len(series)) ** 0.5
            conf_low = [f - 1.28 * std_dev for f in forecast]
            conf_high = [f + 1.28 * std_dev for f in forecast]
            model_name = "Simple exponential smoothing (fallback)"

        cumulative = sum(forecast)
        return {
            "days": days,
            "historical": historical,
            "forecast": forecast,
            "confidence_low": conf_low,
            "confidence_high": conf_high,
            "cumulative_forecast": float(cumulative),
            "model": model_name,
        }
    except ImportError:
        return {
            "days": days,
            "historical": historical,
            "forecast": [],
            "confidence_low": [],
            "confidence_high": [],
            "cumulative_forecast": 0.0,
            "model": "statsmodels not available",
        }
