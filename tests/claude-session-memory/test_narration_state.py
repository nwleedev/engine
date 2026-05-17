from pathlib import Path
import narration_state as ns


def test_initial_count_is_zero(tmp_path):
    assert ns.get_consecutive_failures(tmp_path) == 0


def test_increment_persists(tmp_path):
    ns.increment_failures(tmp_path)
    ns.increment_failures(tmp_path)
    assert ns.get_consecutive_failures(tmp_path) == 2


def test_reset_clears_count(tmp_path):
    ns.increment_failures(tmp_path)
    ns.increment_failures(tmp_path)
    ns.reset_failures(tmp_path)
    assert ns.get_consecutive_failures(tmp_path) == 0


def test_should_use_fallback_when_three_or_more(tmp_path):
    assert ns.should_use_fallback(tmp_path) is False
    for _ in range(3):
        ns.increment_failures(tmp_path)
    assert ns.should_use_fallback(tmp_path) is True
