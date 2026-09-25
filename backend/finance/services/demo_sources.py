"""Sources de démo — toutes marquées simulées."""
from finance.models import (
    Account, Channel, FinancialSource, IntegrationMethod, SourceStatus,
)


DEFAULTS = (
    ("Moov Money", "MOOV", Channel.MOOV, IntegrationMethod.SIMULATED_API, "••••4821"),
    ("T-Money", "TMONEY", Channel.TMONEY, IntegrationMethod.SIMULATED_API, "••••1102"),
    ("Flooz", "FLOOZ", Channel.FLOOZ, IntegrationMethod.SIMULATED_API, "••••7740"),
    ("Banque", "BANQUE", Channel.BANQUE, IntegrationMethod.CSV, "••••9018"),
    ("Caisse", "ESPECES", Channel.ESPECES, IntegrationMethod.MANUAL, ""),
)


def ensure_default_sources(owner) -> list:
    created = []
    org = getattr(owner, "organization", None)
    for name, kind, channel, method, mask in DEFAULTS:
        acc_qs = Account.objects.filter(channel=channel)
        if org is not None:
            acc_qs = acc_qs.filter(organization=org)
        acc = acc_qs.first()
        lookup = {"name": name, "connector_kind": kind}
        defaults = {
            "integration_method": method,
            "account": acc,
            "channel": channel,
            "is_simulated": True,
            "status": SourceStatus.IDLE,
            "merchant_mask": mask,
            "created_by": owner,
            "organization": org,
        }
        if org is not None:
            lookup["organization"] = org
        src, _ = FinancialSource.objects.get_or_create(**lookup, defaults=defaults)
        created.append(src)
    return created
