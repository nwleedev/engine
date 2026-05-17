<!-- SHARED-SKILLS-START -->
## Shared Skills

- Use `shared-skills` when requirements, research, specs, plans, tests, implementation evidence, or completion claims need traceability.
- Use `requirements-packet`, `spec-contract`, `plan-contract`, and `spec-plan-coverage` when broad requirements must become traceable specs, plan tasks, validation methods, and completion evidence.
- Keep a `Spec Ledger` with stable `spec_clause_id` values when broad spec IDs are not enough to prove coverage, and require a `Spec-to-Plan Coverage Matrix` before implementation and completion.
- Treat unresolved `missing_plan`, `missing_validation`, `missing_evidence`, `stale_evidence`, or `unresolved_risk` as blockers for a done claim.
- Route behavior-changing tests through `scenario-test-designer`, `test-plan-contract`, and `tdd-test-writing`; record infeasible automated tests and residual risk in `verification-gate`.
- Use a `Fixture Governance Contract` before adding or expanding fixtures, mocks, fakes, stubs, snapshots, seed records, generated inputs, or test-only adapters.
- Treat the fixture budget as `0` by default; every exception needs linked scenarios, linked spec clauses, a real-boundary alternative, owner, drift check, and expiry or update trigger.
- Treat `unjustified_fixture`, `fixture_overgrowth`, `unapproved_mock`, `stale_fixture`, `missing_real_boundary_check`, and `test_only_behavior` as blocking test-quality findings.
- Keep detailed workflows in the installed shared-skills `SKILL.md` and `references/*`; do not duplicate them in AGENTS.md.
- Use project-local rules when shared-skills is not installed, and report the missing optional plugin only when it affects the task.
- Use the shared-skills install/status diagnostic to check whether this compact block is present and not over-expanded.
<!-- SHARED-SKILLS-END -->
