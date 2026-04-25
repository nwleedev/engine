PYTEST = pytest -q

.PHONY: test test-session-memory test-scripts test-quality-guard test-ref-manager

# Run each plugin test suite in its own process to prevent sys.modules collision
# between plugins that share script filenames.
test: test-session-memory test-scripts test-quality-guard test-ref-manager

test-session-memory:
	$(PYTEST) tests/session-memory/

test-scripts:
	$(PYTEST) tests/scripts/

test-quality-guard:
	$(PYTEST) tests/quality-guard/

test-ref-manager:
	$(PYTEST) tests/ref-manager/