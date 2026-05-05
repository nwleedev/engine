PYTEST = pytest -q

.PHONY: test test-session-memory test-scripts test-quality-guard test-codex-quality-guard test-codex-session-memory test-shared-subagents test-shared-skills

# Run each plugin test suite in its own process to prevent sys.modules collision
# between plugins that share script filenames.
test: test-session-memory test-scripts test-quality-guard test-codex-quality-guard test-codex-session-memory test-shared-skills

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
