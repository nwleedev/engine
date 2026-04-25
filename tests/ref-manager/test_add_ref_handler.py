import subprocess
import sys
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/ref-manager/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


def _run(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "add_ref_handler.py")] + args,
        capture_output=True,
        text=True,
    )


def test_add_ref_url_creates_file_and_index(tmp_path):
    html = b"<html><body><h1>Docs</h1></body></html>"
    resp = mock.MagicMock()
    resp.headers = mock.MagicMock()
    resp.headers.get = mock.MagicMock(return_value="text/html")
    resp.read = mock.MagicMock(return_value=html)
    resp.__enter__ = mock.MagicMock(return_value=resp)
    resp.__exit__ = mock.MagicMock(return_value=False)

    import ref_fetcher
    with mock.patch("ref_fetcher.urllib.request.urlopen", return_value=resp):
        import add_ref_handler
        with mock.patch("add_ref_handler.fetch_url", wraps=ref_fetcher.fetch_url):
            # Call main directly via argparse simulation
            test_args = [
                "https://docs.python.org/typing.html",
                "--name", "python-typing",
                "--topic", "python",
                "--tags", "python", "typing",
                "--cwd", str(tmp_path),
            ]
            with mock.patch("sys.argv", ["add_ref_handler.py"] + test_args):
                with mock.patch("ref_fetcher.urllib.request.urlopen", return_value=resp):
                    add_ref_handler.main()

    index = tmp_path / ".claude" / "refs" / "INDEX.md"
    assert index.exists()
    content = index.read_text(encoding="utf-8")
    assert "python-typing" in content


def test_add_ref_local_file_copies_and_registers(tmp_path):
    src = tmp_path / "report.pdf"
    src.write_bytes(b"%PDF-1.4 test")

    dest_cwd = tmp_path / "project"
    dest_cwd.mkdir()

    import add_ref_handler
    test_args = [
        str(src),
        "--name", "annual-report",
        "--topic", "reports",
        "--cwd", str(dest_cwd),
    ]
    with mock.patch("sys.argv", ["add_ref_handler.py"] + test_args):
        add_ref_handler.main()

    index = dest_cwd / ".claude" / "refs" / "INDEX.md"
    assert index.exists()
    content = index.read_text(encoding="utf-8")
    assert "annual-report" in content
    assert (dest_cwd / ".claude" / "refs" / "reports" / "report.pdf").exists()


def test_add_ref_unsupported_file_exits_nonzero(tmp_path):
    src = tmp_path / "script.py"
    src.write_text("print('hi')", encoding="utf-8")

    import add_ref_handler
    import pytest
    test_args = [
        str(src),
        "--name", "bad-file",
        "--topic", "misc",
        "--cwd", str(tmp_path),
    ]
    with mock.patch("sys.argv", ["add_ref_handler.py"] + test_args):
        with pytest.raises(SystemExit) as exc_info:
            add_ref_handler.main()
    assert exc_info.value.code != 0


def test_add_ref_registers_relative_path(tmp_path):
    src = tmp_path / "notes.md"
    src.write_text("# Notes", encoding="utf-8")

    import add_ref_handler
    test_args = [
        str(src),
        "--name", "project-notes",
        "--topic", "general",
        "--tags", "notes",
        "--cwd", str(tmp_path),
    ]
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with mock.patch("sys.argv", ["add_ref_handler.py"] + test_args):
        with redirect_stdout(buf):
            add_ref_handler.main()

    output = buf.getvalue().strip()
    assert output.startswith(".claude/refs/")
    assert not output.startswith("/")


def test_add_ref_no_tags_still_registers(tmp_path):
    src = tmp_path / "readme.txt"
    src.write_text("readme content", encoding="utf-8")

    import add_ref_handler
    test_args = [
        str(src),
        "--name", "readme",
        "--topic", "docs",
        "--cwd", str(tmp_path),
    ]
    with mock.patch("sys.argv", ["add_ref_handler.py"] + test_args):
        add_ref_handler.main()

    from ref_io import load_index
    entries = load_index(str(tmp_path))
    assert any(e["name"] == "readme" for e in entries)
    readme_entry = next(e for e in entries if e["name"] == "readme")
    assert readme_entry["tags"] == []


def test_add_ref_path_traversal_topic_is_rejected(tmp_path):
    src = tmp_path / "doc.md"
    src.write_text("# Doc", encoding="utf-8")

    import add_ref_handler
    import pytest
    test_args = [
        str(src),
        "--name", "bad",
        "--topic", "../../etc",
        "--cwd", str(tmp_path),
    ]
    with mock.patch("sys.argv", ["add_ref_handler.py"] + test_args):
        with pytest.raises(SystemExit) as exc_info:
            add_ref_handler.main()
    assert exc_info.value.code != 0


def test_add_ref_newline_in_name_is_rejected(tmp_path):
    src = tmp_path / "doc.txt"
    src.write_text("content", encoding="utf-8")

    import add_ref_handler
    import pytest
    test_args = [
        str(src),
        "--name", "bad\nname",
        "--topic", "misc",
        "--cwd", str(tmp_path),
    ]
    with mock.patch("sys.argv", ["add_ref_handler.py"] + test_args):
        with pytest.raises(SystemExit) as exc_info:
            add_ref_handler.main()
    assert exc_info.value.code != 0


def test_add_ref_newline_in_tags_is_rejected(tmp_path):
    src = tmp_path / "doc.txt"
    src.write_text("content", encoding="utf-8")

    import add_ref_handler
    import pytest
    test_args = [
        str(src),
        "--name", "good-name",
        "--topic", "misc",
        "--tags", "bad\ntag",
        "--cwd", str(tmp_path),
    ]
    with mock.patch("sys.argv", ["add_ref_handler.py"] + test_args):
        with pytest.raises(SystemExit) as exc_info:
            add_ref_handler.main()
    assert exc_info.value.code != 0
