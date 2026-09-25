"""
Tests du journal d'audit immuable.
"""
import pytest
from auditing.models import AuditLog
from auditing.services import log_action, verify_chain


@pytest.mark.django_db
def test_audit_log_creates_with_hash():
    """Un AuditLog est créé avec un hash non-nul."""
    entry = log_action(
        action="TEST_ACTION",
        entity="TestEntity",
        entity_id="123",
        details={"foo": "bar"},
    )
    assert entry.hash != "0" * 64
    assert len(entry.hash) == 64  # SHA-256 hex


@pytest.mark.django_db
def test_audit_log_immutable_cannot_update():
    """Une fois créé, un AuditLog ne peut pas être modifié."""
    entry = log_action(action="X", entity="Y", entity_id="1")
    with pytest.raises(PermissionError):
        entry.action = "MODIFIED"
        entry.save()


@pytest.mark.django_db
def test_audit_log_immutable_cannot_delete():
    """Un AuditLog ne peut pas être supprimé."""
    entry = log_action(action="X", entity="Y", entity_id="1")
    with pytest.raises(PermissionError):
        entry.delete()


@pytest.mark.django_db
def test_chain_intact_after_multiple_inserts():
    """La chaîne reste intacte après 5 insertions consécutives."""
    for i in range(5):
        log_action(action=f"TEST_{i}", entity="TestEntity", entity_id=str(i))
    is_intact, broken = verify_chain()
    assert is_intact is True
    assert broken == []


@pytest.mark.django_db
def test_chain_detects_manual_modification():
    """Si on modifie directement la DB (via QuerySet.update), verify_chain détecte la cassure."""
    for i in range(3):
        log_action(action=f"TEST_{i}", entity="TestEntity", entity_id=str(i))

    # Modification directe via QuerySet (bypass .save())
    AuditLog.objects.filter(id=2).update(action="HACKED")

    is_intact, broken = verify_chain()
    assert is_intact is False
    assert len(broken) > 0


@pytest.mark.django_db
def test_prev_hash_chain():
    """Chaque entrée doit avoir prev_hash = hash de l'entrée précédente."""
    e1 = log_action(action="A", entity="X", entity_id="1")
    e2 = log_action(action="B", entity="X", entity_id="2")
    assert e2.prev_hash == e1.hash
