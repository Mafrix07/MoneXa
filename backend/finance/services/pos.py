"""Ingestion POS : factures et paiements via jeton caisse, matcher existant."""
from __future__ import annotations

import hashlib
import secrets
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

from django.utils import timezone as dj_timezone
from django.utils.dateparse import parse_datetime

from auditing.services import log_action
from finance.connectors.base import NormalizedTransaction
from finance.models import Channel, Invoice, InvoiceStatus, PosCredential
from finance.services.ingest import ingest_normalized

POS_TOKEN_PREFIX = "mxpos_live_"


def hash_pos_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_pos_secret() -> tuple[str, str, str]:
    raw = POS_TOKEN_PREFIX + secrets.token_urlsafe(32)
    digest = hash_pos_token(raw)
    hint = raw[-4:]
    return raw, digest, hint


def resolve_pos_token(raw: str) -> PosCredential | None:
    if not raw or not raw.startswith(POS_TOKEN_PREFIX):
        return None
    digest = hash_pos_token(raw)
    return (
        PosCredential.objects.select_related("organization", "created_by")
        .filter(token_hash=digest, revoked_at__isnull=True)
        .first()
    )


def _money(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Montant invalide.") from exc
    if amount <= 0:
        raise ValueError("Le montant doit être strictement positif.")
    return amount.quantize(Decimal("0.01"))


def _channel(value, fallback: str) -> str:
    code = (value or fallback or Channel.ESPECES).upper()
    if code not in Channel.values:
        raise ValueError("Canal inconnu.")
    return code


def ingest_pos_invoice(credential: PosCredential, payload: dict) -> tuple[Invoice, bool]:
    org = credential.organization
    user = credential.created_by
    ticket = str(payload.get("ticket_id") or payload.get("external_id") or "").strip()
    if ticket:
        existing = Invoice.objects.filter(organization=org, pos_ticket_id=ticket).first()
        if existing:
            return existing, False

    client_name = str(payload.get("client_name") or payload.get("customer") or "").strip()
    if not client_name:
        raise ValueError("client_name est requis.")
    amount = _money(payload.get("amount"))
    today = date.today()
    issue = payload.get("issue_date") or today.isoformat()
    due = payload.get("due_date") or (today + timedelta(days=7)).isoformat()
    invoice = Invoice(
        organization=org,
        reference=Invoice.generate_reference(org),
        client_name=client_name[:200],
        client_phone=str(payload.get("client_phone") or payload.get("phone") or "")[:20],
        amount=amount,
        issue_date=date.fromisoformat(str(issue)[:10]),
        due_date=date.fromisoformat(str(due)[:10]),
        status=InvoiceStatus.EMISE,
        pos_ticket_id=ticket,
        created_by=user,
    )
    invoice.save()
    log_action(
        user=user,
        action="FACTURE_POS",
        entity="Invoice",
        entity_id=str(invoice.pk),
        details={"ticket_id": ticket, "reference": invoice.reference, "monexa_ref": invoice.monexa_ref},
    )
    return invoice, True


def ingest_pos_payment(credential: PosCredential, payload: dict):
    org = credential.organization
    user = credential.created_by
    ref = str(payload.get("provider_ref") or payload.get("reference") or payload.get("external_id") or "").strip()
    if not ref:
        raise ValueError("provider_ref est requis.")
    amount = _money(payload.get("amount"))
    channel = _channel(payload.get("channel"), credential.channel)
    paid_at = payload.get("paid_at") or payload.get("occurred_at")
    if paid_at:
        occurred = parse_datetime(str(paid_at)) or datetime.fromisoformat(str(paid_at).replace("Z", "+00:00"))
        if occurred.tzinfo is None:
            occurred = occurred.replace(tzinfo=timezone.utc)
    else:
        occurred = dj_timezone.now()

    mxa = str(payload.get("monexa_ref") or "").strip()
    fact = str(payload.get("invoice_reference") or "").strip()
    ticket = str(payload.get("ticket_id") or "").strip()
    raw_bits = [f"POS {ref}", mxa, fact, ticket]
    tx = NormalizedTransaction(
        source=channel,
        external_id=ref,
        direction="IN",
        amount=amount,
        currency="XOF",
        counterparty=str(payload.get("payer_name") or payload.get("client_name") or "")[:200],
        reference=ref,
        occurred_at=occurred,
        phone=str(payload.get("payer_phone") or payload.get("client_phone") or "")[:20],
        raw_payload={"raw_text": " ".join(b for b in raw_bits if b), "pos": True, "org": org.pk},
    )
    payment, created = ingest_normalized(tx, user)
    if created:
        log_action(
            user=user,
            action="PAIEMENT_POS",
            entity="Payment",
            entity_id=str(payment.pk),
            details={"provider_ref": payment.provider_ref, "channel": payment.channel},
        )
    return payment, created
