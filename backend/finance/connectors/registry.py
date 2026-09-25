from __future__ import annotations

from .base import FinancialConnector
from .csv_connector import CSVConnector
from .manual import ManualConnector
from .simulated import BankConnector, CashConnector, FloozConnector, MoovConnector, TMoneyConnector
from .sms_connector import SMSConnector


_MAP = {
    "TMONEY": TMoneyConnector,
    "MOOV": MoovConnector,
    "FLOOZ": FloozConnector,
    "BANQUE": BankConnector,
    "ESPECES": CashConnector,
    "CSV": CSVConnector,
    "SMS": SMSConnector,
    "MANUAL": ManualConnector,
}


def get_connector(kind: str, **kwargs) -> FinancialConnector:
    cls = _MAP.get(kind.upper())
    if cls is None:
        raise ValueError(f"Connecteur inconnu: {kind}")
    try:
        return cls(**kwargs)
    except TypeError:
        return cls()
