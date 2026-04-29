from pathlib import Path
import sys
import os

# Add scripts dir to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../plugins/session-memory/scripts"))

import migrate as mg


def test_dedup_index_collapses_duplicates(tmp_path):
    sd = tmp_path / "session"
    sd.mkdir()
    body = (
        "---\nsession_id: s\n---\n"
        "# 세션 요약\n\n## 컨텍스트 목록\n\n"
        "- [CONTEXT-X.md] — first\n"
        "- [CONTEXT-X.md] — second\n"
        "- [CONTEXT-X.md] — third\n"
        "- [CONTEXT-Y.md] — alpha\n"
        "---\n"
    )
    (sd / "INDEX.md").write_text(body, encoding="utf-8")
    changed = mg.dedup_index(sd, dry_run=False)
    assert changed is True
    out = (sd / "INDEX.md").read_text(encoding="utf-8")
    assert out.count("[CONTEXT-X.md]") == 1
    assert "third" in out
    assert "first" not in out


def test_dry_run_does_not_modify(tmp_path):
    sd = tmp_path / "session"
    sd.mkdir()
    body = "---\n---\n- [F.md] — a\n- [F.md] — b\n"
    (sd / "INDEX.md").write_text(body, encoding="utf-8")
    mg.dedup_index(sd, dry_run=True)
    out = (sd / "INDEX.md").read_text(encoding="utf-8")
    assert out.count("[F.md]") == 2
