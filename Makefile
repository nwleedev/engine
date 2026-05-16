PYTEST = uv run --isolated --python /usr/local/bin/python3.12 --with pytest pytest -q

.PHONY: test test-session-memory test-scripts test-quality-guard test-quality-guard-source test-codex-quality-guard test-shared-subagents test-shared-skills test-deep-research-prompt-export build-plugins validate-generated test-interop test-harness-foundry-lab

# Run each plugin test suite in its own process to prevent sys.modules collision
# between plugins that share script filenames.
test: test-deep-research-prompt-export test-session-memory test-scripts test-quality-guard test-quality-guard-source test-codex-quality-guard test-shared-skills test-interop test-harness-foundry-lab

test-session-memory:
	$(PYTEST) tests/session-memory/

test-scripts:
	$(PYTEST) tests/scripts/

test-quality-guard:
	$(PYTEST) tests/quality-guard/

test-quality-guard-source:
	$(PYTEST) plugin-sources/quality-guard/adapters/codex/tests/

test-codex-quality-guard:
	$(PYTEST) plugins/codex/quality-guard/tests/

test-shared-subagents:
	$(PYTEST) tests/scripts/test_install_shared_subagents.py tests/scripts/test_print_agents_md_block.py tests/scripts/test_shared_subagents_marketplace.py

test-shared-skills: build-plugins validate-generated
	$(PYTEST) tests/scripts/test_shared_skills_plugin.py

test-deep-research-prompt-export: build-plugins validate-generated
	$(PYTEST) tests/deep-research-prompt-export/

build-plugins:
	python tools/build_plugins.py

validate-generated:
	python tools/validate_generated.py

test-interop:
	$(PYTEST) tests/interop/

test-harness-foundry-lab:
	$(PYTEST) apps/harness-foundry-lab/tests/
