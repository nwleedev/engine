from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import pytest

from learnable.materials.events import append_audit, append_event, read_audits, read_events


def _append_event_in_process(args: tuple[str, int]) -> None:
    events_path, index = args
    append_event(
        Path(events_path),
        event_type="node.created",
        learnable_session_id="learnable-session-001",
        message=f"created node {index}",
        node_id=f"node-{index}",
    )


def _append_audit_in_process(args: tuple[str, int]) -> None:
    audit_path, index = args
    append_audit(
        Path(audit_path),
        request={"path": f"/materials/{index}"},
        action={"type": "read"},
    )


def test_append_event_writes_redacted_jsonl_record(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"

    append_event(
        events_path,
        event_type="node.created",
        learnable_session_id="learnable-session-001",
        message="created with TOKEN=learnable-token-12345",
        node_id="node-root",
    )

    record = json.loads(events_path.read_text(encoding="utf-8"))
    assert record["type"] == "node.created"
    assert record["learnable_session_id"] == "learnable-session-001"
    assert record["node_id"] == "node-root"
    assert record["created_at"].endswith("Z")
    assert "learnable-token-12345" not in record["message"]
    assert "[REDACTED:assignment]" in record["message"]


def test_read_events_returns_appended_events_in_jsonl_order(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    append_event(
        events_path,
        event_type="session.created",
        learnable_session_id="learnable-session-001",
        message="created session",
        node_id="node-root",
    )
    append_event(
        events_path,
        event_type="node.created",
        learnable_session_id="learnable-session-001",
        message="created child",
        node_id="node-child",
    )

    events = read_events(events_path)

    assert [event["type"] for event in events] == [
        "session.created",
        "node.created",
    ]
    assert [event["node_id"] for event in events] == ["node-root", "node-child"]


def test_read_events_returns_empty_list_for_empty_or_missing_jsonl(
    tmp_path: Path,
) -> None:
    empty_path = tmp_path / "empty.jsonl"
    empty_path.write_text("", encoding="utf-8")

    assert read_events(empty_path) == []
    assert read_events(tmp_path / "missing.jsonl") == []


@pytest.mark.parametrize(
    "record",
    [
        {
            "type": "node.created",
            "learnable_session_id": "learnable-session-001",
            "message": "created",
        },
        {
            "created_at": 1,
            "type": "node.created",
            "learnable_session_id": "learnable-session-001",
            "message": "created",
        },
        {
            "created_at": "2026-05-18T00:00:00Z",
            "type": "node.created",
            "learnable_session_id": "learnable-session-001",
            "message": "created",
            "node_id": 1,
        },
    ],
)
def test_read_events_rejects_schema_invalid_records(
    tmp_path: Path,
    record: dict[str, object],
) -> None:
    events_path = tmp_path / "events.jsonl"
    events_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(ValueError):
        read_events(events_path)


def test_concurrent_event_appends_do_not_drop_records(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"

    def append(index: int) -> None:
        append_event(
            events_path,
            event_type="node.created",
            learnable_session_id="learnable-session-001",
            message=f"created node {index}",
            node_id=f"node-{index}",
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(append, range(40)))

    events = read_events(events_path)

    assert len(events) == 40
    assert {event["node_id"] for event in events} == {f"node-{index}" for index in range(40)}


def test_multiprocess_event_appends_do_not_drop_records(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    context = get_context("spawn")

    with context.Pool(processes=4) as pool:
        pool.map(
            _append_event_in_process,
            [(str(events_path), index) for index in range(20)],
        )

    events = read_events(events_path)

    assert len(events) == 20
    assert {event["node_id"] for event in events} == {f"node-{index}" for index in range(20)}


def test_append_audit_writes_redacted_server_audit_without_token(tmp_path: Path) -> None:
    audit_path = tmp_path / ".codex" / "materials" / ".server" / "audits.jsonl"

    append_audit(
        audit_path,
        request={"path": "/materials", "token": "learnable-token-12345"},
        action={"type": "create_session", "message": "Bearer learnable-token-12345"},
    )

    record = json.loads(audit_path.read_text(encoding="utf-8"))
    encoded = json.dumps(record, sort_keys=True)
    assert record["created_at"].endswith("Z")
    assert record["request"]["path"] == "/materials"
    assert "learnable-token-12345" not in encoded
    assert "token" not in record["request"]
    assert "[REDACTED:bearer]" in record["action"]["message"]


def test_read_audits_returns_appended_audits_in_jsonl_order(tmp_path: Path) -> None:
    audit_path = tmp_path / ".codex" / "materials" / ".server" / "audits.jsonl"
    append_audit(
        audit_path,
        request={"path": "/status"},
        action={"type": "status"},
    )
    append_audit(
        audit_path,
        request={"path": "/materials"},
        action={"type": "list"},
    )

    audits = read_audits(audit_path)

    assert [audit["request"]["path"] for audit in audits] == ["/status", "/materials"]


def test_read_audits_returns_empty_list_for_empty_or_missing_jsonl(
    tmp_path: Path,
) -> None:
    empty_path = tmp_path / "audits.jsonl"
    empty_path.write_text("", encoding="utf-8")

    assert read_audits(empty_path) == []
    assert read_audits(tmp_path / "missing-audits.jsonl") == []


@pytest.mark.parametrize(
    "record",
    [
        {"created_at": "2026-05-18T00:00:00Z", "request": {}},
        {"created_at": 1, "request": {}, "action": {}},
        {"created_at": "2026-05-18T00:00:00Z", "request": "status", "action": {}},
        {"created_at": "2026-05-18T00:00:00Z", "request": {}, "action": "status"},
    ],
)
def test_read_audits_rejects_schema_invalid_records(
    tmp_path: Path,
    record: dict[str, object],
) -> None:
    audit_path = tmp_path / "audits.jsonl"
    audit_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(ValueError):
        read_audits(audit_path)


def test_concurrent_audit_appends_do_not_drop_records(tmp_path: Path) -> None:
    audit_path = tmp_path / ".codex" / "materials" / ".server" / "audits.jsonl"

    def append(index: int) -> None:
        append_audit(
            audit_path,
            request={"path": f"/materials/{index}"},
            action={"type": "read"},
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(append, range(40)))

    audits = read_audits(audit_path)

    assert len(audits) == 40
    assert {audit["request"]["path"] for audit in audits} == {
        f"/materials/{index}" for index in range(40)
    }


def test_multiprocess_audit_appends_do_not_drop_records(tmp_path: Path) -> None:
    audit_path = tmp_path / ".codex" / "materials" / ".server" / "audits.jsonl"
    context = get_context("spawn")

    with context.Pool(processes=4) as pool:
        pool.map(
            _append_audit_in_process,
            [(str(audit_path), index) for index in range(20)],
        )

    audits = read_audits(audit_path)

    assert len(audits) == 20
    assert {audit["request"]["path"] for audit in audits} == {
        f"/materials/{index}" for index in range(20)
    }
