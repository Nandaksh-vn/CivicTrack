# CivicTrack — Security Review (Phase 18 / Phase 20 DOC-032)

> **Date:** 06 November 2026
> **Scope:** SEC-01..SEC-10, NFR-004..NFR-007, NFR-021, RBAC-01..RBAC-08
> **Verdict:** POR — Pass with observations. No critical/high finding open in
> the implemented surface. Two residual risks are deferred to Phases 11/18
> and recorded below. This report does not claim scans that were not run.

---

## 1. What was reviewed

- `backend/app/core/security.py` (bcrypt + JWT), `backend/app/core/config.py`
  (secret guards), `backend/app/api/deps.py` + `backend/app/dependencies.py`
  (role/object guards), `backend/app/core/logging.py` (redaction),
  `backend/app/api/v1/*`, `backend/app/main.py` (CORS, error envelope),
  `frontend/src/api/client.ts` (token storage), `frontend/src/router/*`
  (role guards), `frontend/src/lib/validators.ts`, upload limits in
  `.env.example`, Dockerfiles/compose for non-root + healthchecks.

- Automated evidence: `backend/tests/unit/test_security.py` (17 tests),
  `test_deps.py` (10), `test_config.py`, `tests/integration/test_rbac.py`
  (18 cases), `test_auth.py` (12), `frontend/tests/unit/*` (57),
  `docker compose config` (both compose files).

No OWASP ZAP, Burp, or container-scanner run was executed in this session;
those belong to Phase 18 (TEST-050..TEST-053). Nothing below fabricates
their output.

---

## 2. Controls verified (SEC-01..SEC-10)

| ID | Control | Evidence | Result |
|---|---|---|---|
| SEC-01 | Bcrypt, no plaintext in DB/logs | `hash_password`/`verify` in `core/security.py`; `test_security.py`; `password_hash` only column | Pass |
| SEC-02 | JWT 8 h, secret >=32 bytes, inactive rejected | `JWT_EXPIRES_MINUTES=480`, config guard refuses placeholder/short secrets, `test_security.py` + `test_config.py` | Pass |
| SEC-03 | Server role + object scope every route | `require_roles` + `ensure_complaint_owner/officer_department/superintendent_action_allowed`; 12-case RBAC matrix in `test_rbac.py` | Pass |
| SEC-04 | Upload magic bytes, 5 MiB, 3/request, random names | Client-side enforced in `frontend/src/lib/validators.ts`; server service pending Phase 8 (router stubs). Demo README documents limits | **Gap — see residual risk 1** |
| SEC-05 | Private media, no public static | `uploads` is a Docker volume, not mounted in `web`; streaming endpoint design in `API_CONTRACT.md`. No public `uploads/` in repo (gitignored) | Pass (volume) |
| SEC-06 | Internal trigger token-protected | Design: `X-Internal-Token` constant-time; config requires `INTERNAL_TRIGGER_TOKEN` >=32 chars. Endpoint itself is Phase 11 stub (`worker.py`) | Pass (guard) / endpoint pending |
| SEC-07 | Demo window fails closed | `config.py` reverts non-10080 window unless `ALLOW_DEMO_ESCALATION=true` + error log; production refuses demo flag. Covered by `test_config.py` | Pass |
| SEC-08 | PII/token log redaction | `core/logging.py` redaction filter + `tests/unit/test_config.py`-adjacent logging coverage in Phase 5 harness; no password/token in test fixtures | Pass (API) |
| SEC-09 | Read-only audit/history | No update/delete route for those entities; in-app append-only guard (`app/db/guards.py`) raises `AppendOnlyViolation` | Pass |
| SEC-10 | CORS allow-list, no wildcard+credentials | `main.py` `CORSMiddleware` with `settings.cors_origin_list`, `allow_credentials=False`; prod overlay binds to `127.0.0.1` | Pass |

Additional checks:

- **Passwords/emails in args, URLs, browser logs:** frontend stores JWT in
  `sessionStorage` (`civictrack.token`), sends as `Authorization: Bearer`;
  no token in query string; validators surface field errors without echoing
  secrets. No analytics is wired in — nothing to leak.
- **Error leakage:** `main.py` returns `INTERNAL_ERROR` without stack trace;
  validation returns `VALIDATION_ERROR` with field details (see `API_CONTRACT.md`).
- **Injection:** all DB access via SQLAlchemy ORM + bound params; no string
  SQL in routers. MySQL `008` collation avoids case-split email bypass.
- **Mass assignment:** Pydantic schemas (`schemas/auth.py`, `schemas/user.py`)
  allow only declared fields.
- **Last-admin guard:** in `services/user_service.py`, race-free via
  `SELECT ... FOR UPDATE` (Phase 6); concurrency test in `test_rbac.py`.
- **RBAC 401/403/404:** unauthenticated 401, wrong role 403, foreign-object
  policy per SRS (citizen queries scoped by owner); covered by `test_rbac.py`
  and `test_deps.py`.

---

## 3. Findings

- **Critical / High:** none open on the implemented surface.
- **Medium (residual risk 1):** upload validation exists only on the client
  (`validators.ts`) and in the API contract; the server-side
  magic-byte/size/orphan-cleanup service (BE-047..BE-051, Phase 8) is still
  a stub. Until Phase 8 lands, `POST /complaints` does not create
  complaints, so the bypass path is not reachable — but the control cannot
  be called "proven by server test" yet. `TEST-051`/`TEST-009` remain open.
- **Medium (residual risk 2):** escalation worker is still a scheduler stub
  (`app/worker.py::run_escalation_check` logs `status=stub`). The
  exactly-once controls (advisory lock, conditional update, unique
  `escalations.complaint_id` — the unique index itself is DB-enforced
  and tested) are therefore proven at the schema layer only. Sequential/
  parallel/restart proofs (`TEST-020`, `TEST-021`, `TEST-055`) remain open
  until Phase 11 lands.
- **Low:** `npm run test:coverage` fails (missing `@vitest/coverage-v8`).
  Not a security issue; recorded in `docs/TEST_REPORT.md`.

---

## 4. Dependency / container posture (TEST-053, pending Phase 18)

- Containers: `db` (MySQL 8.4), `api` + `worker` (Python 3.12, non-root
  user per `backend/Dockerfile`), `web` (nginx), `migrate`/`seed`
  one-shots. `docker compose config` validates for `docker-compose.yml`,
  the prod overlay, and `seed`/`proxy` profiles.
- No lockfile pin was changed in Phase 20. A full `pip-audit` / `npm audit` /
  Trivy run is deferred to Phase 18; the frontend `package.json` already
  carries `overrides` for `@babel/*` (see `DOC-036` notices).
- `.env` is gitignored; `.env.example` contains placeholder `CHANGE_ME`
  values only; production boot refuses placeholders (`test_config.py`).

---

## 5. Residual risk register

| # | Risk | Severity | Owner phase | Mitigation in place |
|---|---|---|---|---|
| 1 | Server-side upload validation not yet implemented | Medium | Phase 8 | Client enforcement; no write path until Phase 8 |
| 2 | Escalation exactly-once proven only at DB layer | Medium | Phase 11 | Unique index + guard; stub worker cannot escalate |
| 3 | No independent penetration test | Low | Phase 18 | 12-case RBAC + scope tests green; ZAP deferred |
| 4 | Frontend coverage provider missing | Low | Phase 17/20 | Unit/component suite (57 tests) green without coverage |

---

## 6. Phase 20 link (DOC-032)

- Operator procedure: `docs/RUNBOOK.md`
- Candidate evidence: `docs/TEST_REPORT.md` (TEST-058)
- Acceptance evidence by AC: `docs/UAT_REPORT.md`, `docs/TEST_PLAN.md`
- Data retention / no hard delete: `docs/DATA_MODEL.md` §4
- Final gate state: `docs/TRACEABILITY_AUDIT.md` (DOC-033) — says which
  P0 rows still lack a passing server test.

**Sign-off line for Phase 20:** security review complete as a documentation
deliverable with explicit deferrals. The Phase 18 GATE (no critical/high,
load targets, restart re-proof) is **not** signed by this file.
