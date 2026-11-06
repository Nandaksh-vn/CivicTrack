# CivicTrack — Demo Script (Phase 20, DOC-037)

> **Goal:** 5–10 minute walkthrough of the P0 lifecycle:
> submit → accept → progress → escalate → superintendent → resolve.
> **Audience:** evaluators, UAT, handover reviewers.
> **Style:** follow the numbered steps; each ends with a visible check.

---

## 0. Preconditions (2 minutes)

1. Ensure a seeded stack is up:
   ```bash
   cp .env.demo.example .env        # demo window 2 min, visibly labelled
   docker compose up -d --build
   docker compose ps                  # all services healthy
   docker compose run --rm seed python -m app.seed
   docker compose run --rm seed python -m app.seed --check  # CT-2026-100009 overdue
   curl http://localhost:8000/health
   ```
   Web: `http://localhost:8080` (amber "Demo mode" banner when
   `VITE_ALLOW_DEMO_ESCALATION=true`).
2. Log in as demo users (password `Demo@12345`, from `SEED_PASSWORD`):
   - Citizen: `citizen1@demo.local`
   - Officer: `officer.roads@demo.local` (Road Maintenance)
   - Superintendent: `superintendent@demo.local`
   - Admin: `admin@demo.local`
   See `README.md` "Demo deployment" + `docs/RUNBOOK.md` §2 for the
   environment matrix (prod stays at 10080 min).

> **Note on the current tree:** the escalation worker is still a
> Phase 11 stub (`app/worker.py`), so step 4 (auto-escalation) demos the
> *seeded overdue candidate* `CT-2026-100009` and the manual-trigger
> design in `docs/API_CONTRACT.md`. Full auto-escalation needs Phase 11
> (`GET_LOCK` + conditional update). Do not claim auto-escalation works
> until `app/worker.py` calls the escalation service.

---

## 1. Submit (citizen, ~1 minute)

1. Log in as `citizen1@demo.local`.
2. Open "Report a Problem" (`/complaints/new`).
3. Pick category "Pothole / Damaged Road" (routes to Road Maintenance).
4. Enter title (5–150 chars) + description (20–2000 chars), e.g. a large
   pothole near the school gate. Optionally add location + coordinates
   (paired, latitude −90..90, longitude −180..180) and up to 3 images
   (JPEG/PNG/WebP, ≤5 MiB each).
5. Submit once — the button locks while pending.

**Check:** tracking number appears (`CT-YYYY-NNNNNN`); detail shows status
`PENDING_DEPARTMENT_REVIEW`; timeline has two history rows
(`null → SUBMITTED`, `SUBMITTED → PENDING_DEPARTMENT_REVIEW`);
notification NT-01 in the bell. Invalid payload returns 422 with no
complaint and no orphan file (`AC-02`).

---

## 2. Accept (department officer, ~1 minute)

1. Log in as `officer.roads@demo.local`.
2. Open the department queue (`/department`). Your complaint (reported
   above + seeded rows) is visible; other departments are not.
3. Open the complaint, press Accept.

**Check:** status `ACCEPTED`; `accepted_at` set; `resolution_due_at =
accepted_at + sla_seconds` (demo: 2 min to show escalation; prod:
10080 min); NT-02 sent. Cross-department read/mutation by another officer
returns 403 and changes nothing (`AC-14`). Double-accept returns 409.

---

## 3. Progress (department officer, ~1 minute)

1. Still as the roads officer, add a progress note (5–2000 chars).
2. Optionally upload 1–3 evidence images (PROGRESS kind).

**Check:** citizen timeline shows the progress note with actor/time;
NT-04 sent; queue overdue badge counts update (`AC-06`).

---

## 4. Escalate (system, ~1 minute)

Two ways to show this in the demo window:

- **Seeded candidate:** open `CT-2026-100009` (already overdue).
- **Your complaint from step 1:** wait for the demo window to lapse and
  refresh — once Phase 11 is live, the worker escalates it.

**Check:** status `ESCALATED`; escalation row exists (exactly one per
complaint — 20 re-runs still leave one); history row
(`previous → ESCALATED`, actor `SYSTEM`, reason `SLA_BREACH`);
NT-05 to the citizen, the responsible officers, and all active
superintendents; dashboard shows overdue timer (`AC-07`, `AC-08`).

---

## 5. Superintendent (superintendent officer, ~2 minutes)

1. Log in as `superintendent@demo.local`.
2. Open the escalation queue (`/superintendent`). The complaint is sorted
   by overdue duration; overlays show department, acceptance, deadline,
   overdue-at-request-time, and full timeline.
3. Record an action: type `INSTRUCTION` (or `FOLLOW_UP`/`REASSIGN`/`NOTE`),
   note 5–2000 chars, optionally `directed_department_id`. Status does
   not change.

**Check:** action appears in the timeline with identity/time;
NT-06 to the responsible officers + citizen; a superintendent action on a
non-escalated complaint is rejected; resolving from `ESCALATED` is the
only superintendent resolve path (`AC-09`, `AC-10`).

---

## 6. Resolve (officer or superintendent, ~1 minute)

1. As the responsible officer (or as superintendent for an escalated item),
   open Resolve, enter a note (10–2000 chars), optionally attach evidence,
   and confirm.

**Check:** status `RESOLVED`, terminal; `resolved_at`/actor/note recorded;
NT-07 sent; complaint leaves the escalation queue; citizen sees the
resolution in detail + timeline (`AC-11`). Any further mutation returns
409 and mutates nothing.

---

## 7. Close (admin, ~1 minute)

1. Log in as `admin@demo.local`.
2. Open Admin → Users: confirm roles/departments; try to deactivate the
   last active admin — it must be refused.
3. Open Admin → Activity + Audit: confirm status/department counts,
   escalation total, recent events; audit filters work; no update/delete
   route exists for history/audit.

**Check:** deactivation guard message; audit rows append-only;
`PLATFORM_ADMIN`-only routes return 403 to other roles (`AC-13`).

---

## Timing budget

| Step | Time |
|---|---|
| Setup + logins | 2 min |
| Submit | 1 min |
| Accept | 1 min |
| Progress | 1 min |
| Escalate | 1 min |
| Superintendent | 2 min |
| Resolve + admin close | 1–2 min |
| **Total** | **5–10 min** |

If the run reaches step 4 and escalation does not happen on time, check
`docker compose logs worker` for `event=escalation_run`, confirm
`ALLOW_DEMO_ESCALATION=true` + `ESCALATION_WINDOW_MINUTES` in the running
`api`/`worker` environment, and fall back to the seeded
`CT-2026-100009` overdue candidate. See `docs/RUNBOOK.md` §4–§5.
