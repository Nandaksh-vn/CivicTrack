# CivicTrack — Traceability Audit (Phase 20, DOC-033 + DOC-034)

> **Date:** 06 November 2026
> **Method:** (1) ID diff SRS vs Phase 1 baseline, (2) per-FR implementation
> location in this tree, (3) passing test for each implemented row.
> **GATE question:** are all 50 P0 FRs implemented with a passing test?
> **Answer today: no.** This audit proves where the gaps are; it does not
> cover them. Phase 20 therefore cannot be signed `Completed`.

---

## 1. ID diff (scripted audit, Phase 20 re-run of DOC-011)

- SRS inventory: 64 FRs (50 P0 + 7 P1 + 7 P2), 22 NFRs, 20 BRs,
  8 NT triggers, 16 ACs, 44 stories.
- Baseline `docs/TRACEABILITY_BASELINE.md` covers 215/215 SRS requirement IDs
  and 44/44 stories with zero missing and zero duplicates (Phase 1 validator:
  `OVERALL: PASS`).
- This audit adds the implementation + test columns below. P1/P2 rows are
  present so absence is explicit, not silent (DOC-034).

---

## 2. FR audit (P0)

| FR | Owning phase | Implementation in this tree | Passing test | Verdict |
|---|---|---|---|---|
| FR-001 register | 6 | `POST /auth/register` (`api/v1/auth.py` + `services/auth_service.py`) | `test_auth.py` 12 | ✅ |
| FR-002 login/logout | 6 | `POST /auth/login`, `/auth/logout` | `test_auth.py` | ✅ |
| FR-003 bcrypt | 6 | `core/security.py`, cost >=12 | `test_security.py` 17 | ✅ |
| FR-004 role+scope guards | 6 | `api/deps.py`, `require_roles`, scope helpers | `test_rbac.py` 18, `test_deps.py` 10 | ✅ |
| FR-005 `GET /auth/me` | 6 | `api/v1/auth.py` | `test_auth.py` | ✅ |
| FR-006 admin users | 6/13 | `api/v1/admin.py` + `services/user_service.py` | `test_rbac.py` admin + last-admin | ✅ |
| FR-007 `GET /categories` | 8 | **missing** — no categories router; frontend calls `/categories` (404) | none | ❌ stub/gap |
| FR-008 `POST /complaints` | 8 | **stub** — `api/v1/complaints.py` returns dict, no insert | none (only detail stub test) | ❌ |
| FR-009 tracking generator | 8 | **missing** — no `services/tracking.py`; unique DB takes duplicates to `IntegrityError` only | `test_schema_constraints.py` duplicate case | ❌ (constraint only) |
| FR-010 upload validation | 8 | client `validators.ts` only; no storage service | none server-side | ❌ |
| FR-011 coordinates | 8 | DB check constraints present; service validation missing | `test_schema_constraints.py` | ⚠️ DB-only |
| FR-012 routing | 8 | **missing** — no submit transaction | none | ❌ |
| FR-013 submission txn + 2 history | 8 | **missing** | none | ❌ |
| FR-014 `GET /complaints` (citizen) | 9 | **missing** — no list endpoint | none | ❌ |
| FR-015 `GET /complaints/{id}` | 9 | partial — stub returns 5 fields, no images/timeline/department/resolution | `test_complaints.py` (stub expectations) | ⚠️ |
| FR-016 timeline | 9 | **missing** — no `/timeline` | none | ❌ |
| FR-017 department queue | 10 | stub returns `[]` | `test_department_queue.py` (expects `[]` or list shape) | ⚠️ stub |
| FR-018 officer detail scope | 10 | `ensure_officer_department` in stub detail | `test_rbac.py`, `test_complaints.py` | ⚠️ |
| FR-019 accept | 10 | stub returns `ACCEPTED`, no write | `test_complaints.py` | ⚠️ stub |
| FR-020 reject | 10 | stub returns `REJECTED`, no reason validation | `test_complaints.py` | ⚠️ stub |
| FR-021 assign | 10 | **missing** (`POST /assign` not routed) | none | ❌ |
| FR-022 progress | 10 | **missing** | none | ❌ |
| FR-023 `POST /images` | 10 | **missing** | none | ❌ |
| FR-024 resolve | 10/12 | stub returns `RESOLVED`, no state/NT/history write | `test_complaints.py` | ⚠️ stub |
| FR-025 department summary | 10 | **missing** | none | ❌ |
| FR-026 progress on ESCALATED | 10 | **missing** | none | ❌ |
| FR-027 deadline `accepted_at + sla` | 11 | **missing** (seed backdates for demo only) | none | ❌ |
| FR-028 scheduler | 11 | stub `worker.py` logs only | none | ❌ |
| FR-029 exactly-once | 11 | unique `escalations.complaint_id` in DB; lock + conditional update **missing** | `test_schema_constraints.py` (DB layer only) | ⚠️ DB-only |
| FR-030 escalation transition | 11 | stub | none | ❌ |
| FR-031 escalation row | 11 | model exists; no writer | `test_schema_constraints.py` | ⚠️ model-only |
| FR-032 NT-05 fan-out | 11 | **missing** (`services/notification_service.py` absent) | none | ❌ |
| FR-033 config guard | 11 | `core/config.py` (fail-closed, demo flag) | `test_config.py` | ✅ |
| FR-034 `POST /internal/escalations/run` | 11 | **missing** | none | ❌ |
| FR-035 superintendent queue | 12 | stub returns `[]` | `test_superintendent_queue.py` | ⚠️ stub |
| FR-036 escalated detail | 12 | stub detail only | partial | ⚠️ |
| FR-037 timeline read (sup) | 12 | **missing** | none | ❌ |
| FR-038 superintendent action | 12 | stub returns `ACTION_RECORDED` (id 1), no `officer_actions` row | `test_complaints.py` | ⚠️ stub |
| FR-039 directed follow-up | 12 | model `directed_department_id` exists; no writer | none | ❌ writer missing |
| FR-040 queue retention | 12 | design only | none | ❌ |
| FR-041 superintendent resolve | 12 | stub (same as FR-024) | `test_complaints.py` | ⚠️ stub |
| FR-042 transactional notifications | 7 | **missing** — no service, no `notify_users` | none | ❌ |
| FR-043 `GET /notifications` | 7 | **missing** | none | ❌ |
| FR-044 mark read / read-all | 7 | **missing** | none | ❌ |
| FR-045 NT templates | 7 | **missing** | none | ❌ |
| FR-046 departments admin | 13 | **missing** (no `/admin/departments`) | none | ❌ |
| FR-047 categories admin | 13 | stub `POST /admin/categories` only | none | ❌ |
| FR-048 `/admin/activity` | 13 | **missing** | none | ❌ |
| FR-049 `/admin/audit-logs` | 13 | **missing** | none | ❌ |
| FR-050 history writer (append-only) | 8-12 | guard `db/guards.py` + models; writer **missing** (no service writes rows) | `test_schema_constraints.py` (rejection only) | ⚠️ guard-only |

**Count:** 8 ✅ (FR-001..006, FR-033, FR-004-family), 12 ⚠️ (stub/DB-only/partial),
30 ❌ missing. All 50 P0 IDs are assigned (coverage of *scope*), but only
the auth/config subset has an implemented + tested path today. **AC-02..AC-12,
AC-15 cannot be demonstrated end-to-end against the live backend** until
Phases 7-13 land; `AC-01, AC-13, AC-14, AC-16` are the ones with live
evidence (`test_auth.py`, `test_rbac.py`, `test_config.py`, `UAT_REPORT.md`
Phase 17 tree — re-verified in `TEST_REPORT.md`).

### Why UAT_REPORT says "AC-01..AC-16 verified"

`docs/UAT_REPORT.md` (Phase 17) records AC evidence against the delta that
existed when it was written (including tests that lived on that branch).
The current `main`-line tree's pycache shows those test files were removed
or are absent (`test_escalation.py`, `test_notifications.py`,
`test_schema.py`, `test_migrations.py`, `test_append_only.py` — present as
pycache only). Phase 20 re-ran the suite that actually exists today and
found 125 passes, but that suite does not cover the deleted files' scope.
This audit uses only the files present now. Re-establishing the missing
test files is part of closing Phases 7-13, not a Phase 20 paperwork fix.

---

## 3. NFR / BR / NT / AC / story rollup

| Family | Scope | Status today |
|---|---|---|
| NFR-001 performance | Phase 18 | not measured (`PERFORMANCE_REPORT.md`) |
| NFR-002 timeliness | Phase 11 | config + seed only; worker stub |
| NFR-003 concurrency | Phase 11 | DB unique only; 20x/parallel tests missing |
| NFR-004 credential security | Phase 6 | ✅ bcrypt + tests |
| NFR-005 authorization | Phases 6, 18 | ✅ 12-case RBAC; IDOR probe (TEST-050) pending Phase 18 |
| NFR-006 session security | Phase 6 | ✅ 8 h, secret guard |
| NFR-007 privacy | Phases 6, 9, 18 | ◐ scoped reads on stubs; field-level tests pending |
| NFR-008 audit immutability | Phases 13, 17 | ◐ guard present; audit API missing |
| NFR-009 time handling | Phase 5 | ◐ UTC helpers; `DATETIME` storage yes, `DATETIME(6)` doc-only |
| NFR-010 usability | Phases 14, 15, 17 | ✅ 360 px + timed ≤60 s in Phase 15 evidence; frontend suite green |
| NFR-011 reliability | Phases 11, 19 | ◐ volumes + restart config; worker catch-up missing |
| NFR-012 transactional integrity | Phases 7, 8, 10, 11 | ◐ auth txn; complaint/notify txn missing |
| NFR-013 upload safety | Phase 8 | ◐ client-only (see SECURITY_REVIEW risk 1) |
| NFR-014 compatibility | Phase 17 | ◐ Chromium evidence; Firefox/WebKit binaries blocked |
| NFR-015 accessibility | Phases 14, 17, 18 | ✅ axe clean on shell/forms; full-screen re-scan pending |
| NFR-016 maintainability | Phases 3, 20 | ✅ strict TS, ruff, schemas, env contract |
| NFR-017 portability | Phases 3, 19 | ✅ compose config valid; fresh-clone boot needs live DB |
| NFR-018 observability | Phases 5, 11, 19 | ✅ `/health`, `/health/ready`, structured logs, request IDs |
| NFR-019 retention | Phases 4, 13 | ✅ no hard-delete routes; deactivation via `is_active` |
| NFR-020 testability | Phase 17 | ✅ 125 BE + 57 FE green; E2E pending in this tree |
| NFR-021 log hygiene | Phases 5, 18 | ✅ redaction; full log scan pending |
| NFR-022 capacity | Phases 4, 18, 19 | ⚠️ limits in env contract; 500/100 + 2 GB not run |
| BR-01..BR-20 | Phases 4, 6, 8-13 | ◐ DB checks (01, 05, 08, 11-coords, 16-state design) + guards; workflow BRs pending writers |
| NT-01..NT-08 | Phases 7-12, 21 | ❌ templates/recipients/atomicity not implemented (models only) |
| AC-01..AC-16 | Phases 6-18 | ◐ AC-01, 13, 14, 16 live; rest blocked on backend stubs (see §2) |
| 39 P0 stories | Phases 6-15 | ◐ UI present for all; backend paths for most missing |
| SEC-01..SEC-10 | see SECURITY_REVIEW | ◐ 8 pass, 2 gaps with residual risks |

---

## 4. P1 / P2 policy (DOC-034) — explicit

**P1 (FR-051..FR-057; `US-CIT-16`, `US-P1-01`..`US-P1-04`; Phase 21).**
Status: **optional-gated, not started.** No `BE-093..BE-100` or
`FE-039..FE-044` code exists; no `VITE_ENABLE_*` / `GEMINI_*` config in
`.env.example`. Rationale: entry gate requires Phase 20 GATE sign-off plus
explicit approval; P1 must stay behind feature flags with silent fallbacks
and P0 regression green on/off. Nothing in P1 may be implemented until
the 30 missing P0 rows in §2 are closed.

**P2 (FR-058..FR-064).** Status: **not built, future only.** Table:
outbound channels/outbox, multi-tenancy, working-day calendars, image
verification, public transparency portal, native mobile, external
work-order integration. No P0/P1 acceptance references these.

---

## 5. Phase 20 GATE disposition

- **Zero missing P0 requirements (scope):** PASS — every ID is assigned
  (50 P0 + 7 P1 + 7 P2).
- **Zero missing P0 implementations with passing tests:** FAIL —
  30 missing + 12 partial (see §2).
- **Every AC with evidence:** FAIL — AC-02..AC-12, AC-15 blocked.
- **Fresh clone + tests pass:** PARTIAL — unit/component suites pass;
  backend stub endpoints return 200 with empty/placeholder payloads, so the
  demo script's steps 1-6 cannot be rehearsed against live data yet.
- **Release tagged `v1.0.0-p0`:** WITHHELD — tagging a 30-gap gap list as
  the final P0 would misrepresent it. `CHANGELOG.md` records the
  documentation baseline; tag when §2 gaps close.

**Disposition:** Phase 20 documentation is complete up to this audit;
the code GATE is **not** signed. Next actions belong to Phases
4 (already in flight: `0002_full_schema` + guards + constraint tests),
5, 7, 8, 9, 10, 11, 12, 13, 16, 18, 19 before a re-run of this audit.

---

## 6. How to make this table green

1. Land services `complaint_service` / `tracking` / `storage_service`,
   `notification_service`, `escalation_service` + `GET_LOCK` worker,
   `timeline_service`, department/superintendent/admin bodies (Phases 7-13).
2. Wire `internal/escalations/run` + `escalation-status` (Phase 11).
3. Restore or recreate the missing test files
   (`test_escalation.py`, `test_notifications.py`, `test_schema.py`,
   `test_migrations.py`, `test_append_only.py`, `test_uploads.py`,
   `test_complaint_create.py`, `test_citizen_tracking.py`,
   `test_department_flow.py`, `test_superintendent.py`, `test_admin.py`) —
   current pycache proves they existed once.
4. Run Phase 18 hardening + load, Phase 17 E2E, then re-run this audit;
   only then tag `v1.0.0-p0`.
