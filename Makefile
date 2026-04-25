PYTEST = pytest -q

.PHONY: test test-better-research test-domain-professor test-session-memory test-scripts test-harness-builder test-nondev-builder test-quality-guard test-ref-manager

# Run each plugin test suite in its own process to prevent sys.modules collision
# between plugins that share script filenames.
test: test-better-research test-domain-professor test-session-memory test-scripts test-harness-builder test-nondev-builder test-quality-guard test-ref-manager

test-better-research:
	$(PYTEST) tests/better-research/

test-domain-professor:
	$(PYTEST) tests/domain-professor/

test-session-memory:
	$(PYTEST) tests/session-memory/

test-scripts:
	$(PYTEST) tests/scripts/

test-harness-builder:
	$(PYTEST) tests/harness-builder/

test-nondev-builder:
	$(PYTEST) tests/nondev-builder/

test-quality-guard:
	$(PYTEST) tests/quality-guard/

test-ref-manager:
	$(PYTEST) tests/ref-manager/