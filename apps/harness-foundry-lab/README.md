# harness-foundry-lab

Repo-local maintainer app for evaluating `harness-foundry`.

## Purpose

`harness-foundry-lab` owns evaluation corpus, lab-only validation scripts, and evaluation report rendering for `harness-foundry`. It is not an installable Codex plugin.

## Boundaries

- Do not place plugin runtime skills here.
- Do not copy private source project code, customer data, credentials, or internal documents into the corpus.
- Synthetic corpus must be public-safe.
- Cloned repositories under `corpus/domain-harness/repos/` are local evaluation inputs and must not be committed.

## Verification

Maintainer package boundary validation:

```bash
rtk python3 apps/harness-foundry-lab/scripts/validate_plugin_package.py
```

Maintainer corpus wrapper validation:

```bash
rtk python3 apps/harness-foundry-lab/scripts/validate_domain_harness_corpus.py apps/harness-foundry-lab/corpus/domain-harness/synthetic/valid-dev
```

Lab tests:

```bash
rtk pytest apps/harness-foundry-lab/tests
```
