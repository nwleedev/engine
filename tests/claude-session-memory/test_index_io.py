from pathlib import Path
import index_io as idx


def test_create_and_read_index(tmp_path):
    sd = tmp_path / "session1"
    fm = idx.create_index(sd, "abc123", "/some/cwd")
    assert (sd / "INDEX.md").exists()
    assert (sd / "contexts").is_dir()
    read = idx.read_index(sd)
    assert read["session_id"] == "abc123"


def test_atomic_write_no_partial_on_crash(tmp_path):
    sd = tmp_path / "s"
    idx.create_index(sd, "id", "/cwd")
    for i in range(20):
        idx.update_entry(sd, f"FILE{i % 5}.md", f"line {i}", last_uuid=f"u{i}", new_head="")
    fm = idx.read_index(sd)
    assert fm["session_id"] == "id"


def test_dedup_by_filename(tmp_path):
    sd = tmp_path / "s"
    idx.create_index(sd, "id", "/cwd")
    idx.update_entry(sd, "CONTEXT-X.md", "first version", last_uuid="u1", new_head="")
    idx.update_entry(sd, "CONTEXT-X.md", "second version", last_uuid="u2", new_head="")
    idx.update_entry(sd, "CONTEXT-Y.md", "another", last_uuid="u3", new_head="")
    body = (sd / "INDEX.md").read_text(encoding="utf-8")
    assert body.count("[CONTEXT-X.md]") == 1
    assert "second version" in body
    assert "first version" not in body
    assert body.count("[CONTEXT-Y.md]") == 1


def test_started_uuid_persisted(tmp_path):
    sd = tmp_path / "s"
    fm = idx.create_index(sd, "id", "/cwd", started_uuid="first-uuid")
    read = idx.read_index(sd)
    assert read.get("started_uuid") == "first-uuid"


def test_rotation_detected_when_started_uuid_differs(tmp_path):
    sd = tmp_path / "s"
    idx.create_index(sd, "id", "/cwd", started_uuid="old-uuid")
    rotated = idx.detect_rotation(sd, current_first_uuid="new-uuid")
    assert rotated is True


def test_no_rotation_when_started_uuid_matches(tmp_path):
    sd = tmp_path / "s"
    idx.create_index(sd, "id", "/cwd", started_uuid="same-uuid")
    rotated = idx.detect_rotation(sd, current_first_uuid="same-uuid")
    assert rotated is False
