PYTEST = pytest -q

.PHONY: test test-session-memory test-scripts test-quality-guard

# Run each plugin test suite in its own process to prevent sys.modules collision
# between plugins that share script filenames.
test: test-session-memory test-scripts test-quality-guard

test-session-memory:
	$(PYTEST) tests/session-memory/

test-scripts:
	$(PYTEST) tests/scripts/

test-quality-guard:
	$(PYTEST) tests/quality-guard/