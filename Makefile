PYTEST = pytest -q

.PHONY: test test-session-memory test-scripts test-quality-guard test-codex-quality-guard test-codex-session-memory test-shared-subagents test-shared-skills build-plugins validate-generated test-interop

# Run each plugin test suite in its own process to prevent sys.modules collision
# between plugins that share script filenames.
test: test-session-memory test-scripts test-quality-guard test-codex-quality-guard test-codex-session-memory test-shared-skills test-interop

test-session-memory:
	$(PYTEST) tests/session-memory/

test-scripts:
	$(PYTEST) tests/scripts/

test-quality-guard:
	$(PYTEST) tests/quality-guard/

test-codex-quality-guard:
	$(PYTEST) plugins/codex-quality-guard/tests/

test-codex-session-memory:
	$(PYTEST) tests/codex-session-memory/

test-shared-subagents:
	$(PYTEST) tests/scripts/test_install_shared_subagents.py tests/scripts/test_print_agents_md_block.py tests/scripts/test_shared_subagents_marketplace.py

test-shared-skills:
	$(PYTEST) tests/scripts/test_shared_skills_plugin.py

build-plugins:
	python tools/build_plugins.py

validate-generated:
	python tools/validate_generated.py

test-interop:
	$(PYTEST) tests/interop/
