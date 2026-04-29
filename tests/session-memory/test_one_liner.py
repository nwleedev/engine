import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent.parent / "plugins/session-memory/scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import one_liner as ol


def test_simple_first_sentence_english():
    assert ol.extract("This is first. This is second.") == "This is first"


def test_simple_first_sentence_korean():
    assert ol.extract("첫 번째 문장이다。두 번째 문장이다。") == "첫 번째 문장이다"


def test_protects_eg_abbreviation():
    text = "We use foo, e.g. bar and baz. The next sentence."
    assert ol.extract(text) == "We use foo, e.g. bar and baz"


def test_protects_ie_etc_cf():
    assert ol.extract("Foo, i.e. bar etc. is fine. Next.") == "Foo, i.e. bar etc. is fine"


def test_truncates_at_80_chars():
    long = "a" * 200 + ". next."
    assert len(ol.extract(long)) == 80


def test_empty_input():
    assert ol.extract("") == ""


def test_falls_back_when_no_terminator():
    assert ol.extract("no terminator here") == "no terminator here"
