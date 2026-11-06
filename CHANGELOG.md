# Changelog — CivicTrack

All notable changes to this project will be documented in this file.
Format: Keep a Changelog + Semantic Versioning. Unreleased P0 work is
tracked in `tracker-checklist.md` and mapped in
`docs/TRACEABILITY_AUDIT.md`.

## [Unreleased] — Documentation baseline (Phase 20, 2026-11-06)

### Added
- `docs/DATA_MODEL.md` (final): 11-table ERD, FK/delete table, uniques,
  checks, indexes; corrected to `0001_initial -> 0002_full_schema`,
  `app/seed.py`, `test_schema_constraints.py`.
- `docs/SECURITY_REVIEW.md` (DOC-032): SEC-01..SEC-10 review, 2 residual
  risks (server upload validation, escalation exactly-once at DB layer).
- `docs/PERFORMANCE_REPORT.md` (DOC-032): targets + measured coverage
  (58% backend); load/p95 owed to Phase 18.
- `docs/TRACEABILITY_AUDIT.md` (DOC-033 + DOC-034): per-FR implementation
  + test matrix; P1 optional-gated / P2 not-built policy; GATE disposition
  (not signed — 30 missing + 12 partial P0 rows).
- `docs/DEMO_SCRIPT.md` (DOC-037): 5-10 min submit → accept → progress →
  escalate → superintendent → resolve + admin close.
- `docs/TEST_REPORT.md` (TEST-058): 125 backend + 57 frontend green,
  typecheck/lint clean; E2E + frontend coverage explicitly not run.
- `docs/HANDOVER.md` (DOC-039): receiver checklist, fresh-clone steps,
  signature block.
- `THIRD_PARTY_NOTICES.md` (DOC-036) + `LICENSE` (MIT).
- `CHANGELOG.md` (this file, DOC-038 preparation).

### Changed
- `docs/ARCHITECTURE.md` v1.0 and `docs/API_CONTRACT.md` v1.0: finalization
  notes (no contract change). `docs/RUNBOOK.md` / `docs/UAT_REPORT.md` /
  `docs/TEST_PLAN.md` linked; no content change required beyond links.
- `README.md`: Final-delivery section (overview, env vars, demo
  credentials, test commands, P1/P2 status, doc links) — see DOC-030.

### Cleanup (DOC-035)
- `ruff format` on `backend/alembic/versions/0002_full_schema.py` and
  `backend/app/models/complaint_status_history.py`.
- Verified: no tracked `.env`, no TODOs in P0 paths beyond the documented
  worker stub, no committed large artifacts (cache/dist are gitignored).

### Untracked / in-flight (not in this release)
- `backend/alembic/versions/0002_full_schema.py`,
  `backend/app/db/guards.py`, 6 new models, `backend/app/models/__init__.py`
  + `complaint.py` check constraints, `backend/tests/integration/
  test_schema_constraints.py` (Phase 4 DB-007..DB-023). Must be committed
  before any `v1.0.0-p0` tag.

## [v1.0.0-p0] — NOT RELEASED

Release tag withheld. Outstanding code GATE: 30 missing + 12 partial
P0 rows in `docs/TRACEABILITY_AUDIT.md` (§2). Tag when those close and
the audit is re-run with E2E green.
