PYTEST = python3 -m pytest -q

.PHONY: test test-harness-builder

test: test-harness-builder

test-harness-builder:
	$(PYTEST) tests/harness-builder/
