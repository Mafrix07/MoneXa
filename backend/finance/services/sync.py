"""Synchronisation d'une FinancialSource via son connecteur (idempotente)."""
from __future__ import annotations

from django.utils import timezone

from finance.connectors.registry import get_connector
from finance.models import ConnectorSync, FinancialSource, SourceStatus, SyncStatus
from finance.services.ingest import ingest_normalized


def sync_source(source: FinancialSource, user) -> ConnectorSync:
    started = timezone.now()
    log = ConnectorSync.objects.create(
        source=source,
        status=SyncStatus.RUNNING,
        cursor_before=source.cursor or "",
    )
    try:
        connector = get_connector(source.connector_kind)
        health = connector.health_check()
        if not health.get("ok"):
            raise RuntimeError(health.get("detail") or "health_check failed")

        created = 0
        ignored = 0
        rows, next_cursor = connector.fetch_transactions(cursor=source.cursor or None)
        for row in rows:
            tx = connector.normalize(row)
            if tx.direction == "OUT":
                ignored += 1
                continue
            _, was_created = ingest_normalized(tx, user)
            if was_created:
                created += 1
            else:
                ignored += 1

        log.created_count = created
        log.ignored_count = ignored
        log.cursor_after = next_cursor or source.cursor or ""
        log.status = SyncStatus.SUCCESS
        log.finished_at = timezone.now()
        log.save()

        source.cursor = log.cursor_after
        source.last_sync_at = started
        source.last_success_at = log.finished_at
        source.last_error = ""
        source.status = SourceStatus.ACTIVE
        source.save(update_fields=[
            "cursor", "last_sync_at", "last_success_at", "last_error", "status",
        ])
        return log
    except Exception as exc:
        log.status = SyncStatus.ERROR
        log.error_message = str(exc)
        log.finished_at = timezone.now()
        log.save()
        source.last_sync_at = started
        source.last_error = str(exc)
        source.status = SourceStatus.ERROR
        source.save(update_fields=["last_sync_at", "last_error", "status"])
        return log
