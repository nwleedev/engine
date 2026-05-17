from __future__ import annotations


def test_learnable_package_imports() -> None:
    import learnable

    assert learnable.__version__ == "0.1.0"
