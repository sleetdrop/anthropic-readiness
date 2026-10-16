"""Frozen plans and admission survive retries, expiry and concurrent callers."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from anthropic_readiness.config import load_target
from anthropic_readiness.jobs.store import JobStore
from anthropic_readiness.models import JsonObject
from anthropic_readiness.operations.models import FrozenPlan
from anthropic_readiness.operations.reduction import objects

NOW = datetime(2026, 10, 17, tzinfo=UTC)
SESSION = "a" * 64
OTHER = "b" * 64
ROOT = Path(__file__).resolve().parents[2]


def target() -> JsonObject:
    return load_target(ROOT / "examples/target.yaml").to_json()


def preview(store: JobStore, *, now: datetime = NOW) -> FrozenPlan:
    return store.create_plan(target(), ("anthropic-basic",), SESSION, now=now)


def test_duplicate_start_after_lost_reply_is_one_job(tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    plan = preview(store)
    first = store.admit(plan.id, SESSION, "synthetic-start-1", now=NOW)
    assert first.created is True
    retried = JobStore(tmp_path).admit(
        plan.id, SESSION, "synthetic-start-1", now=NOW + timedelta(days=1)
    )
    assert retried.created is False
    assert retried.job == first.job
    other_plan = preview(store)
    with pytest.raises(ValueError, match="idempotency_mismatch"):
        store.admit(other_plan.id, SESSION, "synthetic-start-1", now=NOW)
    new_key = store.admit(plan.id, SESSION, "synthetic-start-2", now=NOW)
    assert new_key.created is False
    assert new_key.job.id == first.job.id
    assert len(objects(store.history({}, None)["items"])) == 1
    assert not (tmp_path / "runs" / first.job.id / "assessment").exists()


def test_capacity_is_one_active_plus_eight_waiting(tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    active = store.admit(preview(store).id, SESSION, "active", now=NOW).job
    store.transition(active.id, "queued", "running")
    queued = [
        store.admit(preview(store).id, SESSION, f"queued-{index}", now=NOW).job
        for index in range(8)
    ]
    with pytest.raises(ValueError, match="queue_full"):
        store.admit(preview(store).id, SESSION, "overflow", now=NOW)
    assert store.get_admitted_plan(queued[0].id).id == queued[0].plan_id
    with pytest.raises(ValueError, match="plan_expired"):
        store.get_plan(queued[0].plan_id, SESSION, now=NOW + timedelta(hours=1))
    assert store.get_job(queued[0].id).state == "queued"
    with pytest.raises(ValueError, match="active_job_exists"):
        store.transition(queued[0].id, "queued", "running")


def test_presets_cannot_change_old_plan(tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    document = target()
    preset_id = store.save_preset(None, document)
    frozen = preview(store)
    path = tmp_path / "plans" / (frozen.id + ".json")
    original = path.read_bytes()
    document["model"] = "changed-synthetic-model"
    assert store.save_preset(preset_id, document) == preset_id
    assert store.presets()[0]["target"] == document
    assert path.read_bytes() == original
    assert store.get_plan(frozen.id, SESSION, now=NOW).config_sha256 == frozen.config_sha256


def test_expired_or_foreign_plan_is_rejected(tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    frozen = preview(store)
    assert store.get_plan(frozen.id, SESSION, now=NOW + timedelta(seconds=899)).id == frozen.id
    with pytest.raises(ValueError, match="plan_expired"):
        store.get_plan(frozen.id, SESSION, now=NOW + timedelta(seconds=900))
    with pytest.raises(ValueError, match="plan_not_found"):
        store.admit(frozen.id, OTHER, "foreign", now=NOW)
    with pytest.raises(ValueError, match="plan_expired"):
        store.admit(frozen.id, SESSION, "expired", now=NOW + timedelta(seconds=900))
    assert not objects(store.history({}, None)["items"])


def test_concurrent_duplicate_admission_has_exactly_one_creator(tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    frozen = preview(store)

    def admit(index: int) -> tuple[str, bool]:
        result = JobStore(tmp_path).admit(frozen.id, SESSION, "same-operation", now=NOW)
        return result.job.id, result.created

    with ThreadPoolExecutor(max_workers=6) as pool:
        admissions = list(pool.map(admit, range(6)))
    assert len({identity for identity, _ in admissions}) == 1
    assert sum(created for _, created in admissions) == 1


def test_history_paging_filters_and_terminal_immutability(tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    for index in range(3):
        frozen = preview(store, now=NOW + timedelta(seconds=index))
        job = store.admit(
            frozen.id, SESSION, f"operation-{index}", now=NOW + timedelta(seconds=index)
        ).job
        store.transition(job.id, "queued", "cancelled")
        with pytest.raises(ValueError, match="illegal_job_transition"):
            store.transition(job.id, "cancelled", "running")
    page = store.history({"state": "cancelled"}, None, limit=2)
    cursor = page["next_cursor"]
    assert isinstance(cursor, str)
    next_page = store.history({"state": "cancelled"}, cursor, limit=2)
    rows = [*objects(page["items"]), *objects(next_page["items"])]
    assert len(rows) == 3
    assert next_page["next_cursor"] is None
    assert not objects(store.history({"model": "' OR 1=1 --"}, None)["items"])
    with pytest.raises(ValueError, match="invalid_history_cursor"):
        store.history({}, cursor)
    with pytest.raises(ValueError, match="invalid_history_limit"):
        store.history({}, None, limit=101)


def test_changed_or_symlinked_plan_cannot_be_admitted(tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    frozen = preview(store)
    path = tmp_path / "plans" / (frozen.id + ".json")
    path.write_text(path.read_text().replace("example-model", "changed-model"))
    with pytest.raises(ValueError, match="plan_integrity"):
        store.admit(frozen.id, SESSION, "changed-plan", now=NOW)
    path.unlink()
    outside = tmp_path / "outside.json"
    outside.write_text("{}")
    path.symlink_to(outside)
    with pytest.raises(ValueError, match="symlink"):
        store.get_plan(frozen.id, SESSION, now=NOW)


def test_invalid_config_and_secret_fields_are_not_persisted(tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    document = target()
    document["credential"] = "synthetic-forbidden-secret"
    with pytest.raises(ValueError, match="schema"):
        store.save_preset(None, document)
    with pytest.raises(ValueError, match="schema"):
        store.create_plan(document, ("anthropic-basic",), SESSION, now=NOW)
    assert all(
        b"synthetic-forbidden-secret" not in path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
