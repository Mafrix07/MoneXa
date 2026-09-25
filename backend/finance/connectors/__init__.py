"""
Connector layer — sources financières → ledger unifié.

Aucun connecteur n'appelle une API opérateur réelle. Les classes
Simulated* reproduisent le contrat d'une future intégration.
"""
from .base import FinancialConnector, NormalizedTransaction
from .csv_connector import CSVConnector
from .manual import ManualConnector
from .registry import get_connector
from .simulated import (
    BankConnector,
    CashConnector,
    FloozConnector,
    MoovConnector,
    TMoneyConnector,
)
from .sms_connector import SMSConnector

__all__ = [
    "FinancialConnector",
    "NormalizedTransaction",
    "CSVConnector",
    "ManualConnector",
    "SMSConnector",
    "TMoneyConnector",
    "MoovConnector",
    "FloozConnector",
    "BankConnector",
    "CashConnector",
    "get_connector",
]
