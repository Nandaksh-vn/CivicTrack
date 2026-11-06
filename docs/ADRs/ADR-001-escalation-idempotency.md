# ADR-001 ΓÇö Exactly-once escalation under concurrency

- **Status:** Accepted
- **Date:** 06 November 2026
- **Phase:** 2 (design), implemented in Phase 9
- **Deciders:** Architecture workstream (DOC), backend workstream (BE)
- **References:** FR-028, FR-029, FR-030, FR-031; SRS ESC-01ΓÇªESC-12, IDEM-01ΓÇªIDEM-04; TRD ┬º13; ARCHITECTURE ┬º6; STATE_MACHINE T7ΓÇôT8

---

## Context

The escalation worker runs on an interval and escalates accepted complaints whose `resolution_due_at` has passed. Three independent failure modes can produce a duplicate escalation:

1. **Overlapping runs** ΓÇö a slow run is still executing when the next interval fires, or two containers start against the same database.
2. **Stale selection** ΓÇö a complaint is selected as a candidate, then resolved by an officer before the update executes.
3. **Replay/restart** ΓÇö the worker restarts mid-run and re-reads candidates it already processed.

A duplicate escalation would create two `escalations` rows, two NT-05 notification sets, and contradictory Superintendent queues. The demo also needs the operation to be safely re-triggerable by hand.

## Decision

Escalation is a **deterministic function of persisted state** and is made idempotent by four independent guards, all of which must hold:

1. **Advisory lock** ΓÇö `SELECT GET_LOCK('civictrack:escalation', 0)` on a dedicated connection. A run that cannot acquire the lock returns `{lock_skipped: true}` and does no work.
2. **Candidate predicate excludes existing escalations** ΓÇö `NOT EXISTS (SELECT 1 FROM escalations e WHERE e.complaint_id = c.id)`.
3. **Conditional update under row lock** ΓÇö inside a per-candidate transaction, `SELECT ... FOR UPDATE`, then re-check `status IN (ACCEPTED, IN_PROGRESS)` and `resolution_due_at <= now_utc`. If either fails, roll back and count as `skipped`.
4. **Database uniqueness** ΓÇö `UNIQUE(escalations.complaint_id)` as the last line of defence. An `IntegrityError` on insert is caught, that candidate is rolled back, and the run continues.

Each candidate gets its **own transaction** so one bad row cannot roll back the batch. The lock is released in `finally`. The manual internal trigger calls the exact same `run_escalation_check(TriggerSource.MANUAL_TRIGGER)`; a second call naturally returns zeros.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| `SELECT ... FOR UPDATE SKIP LOCKED` on the candidate query | MySQL support exists but still needs the unique index for replay safety; simpler to lock per candidate and let the unique constraint arbitrate. |
| Application-level distributed lock (Redis) | Adds an infrastructure dependency the project does not otherwise need; MySQL already owns the state. |
| Scheduler `max_instances=1` alone | Protects one process, not two containers, a restart, or a manual trigger racing the scheduler. |
| Status-only guard without unique index | A crash between status update and escalation insert could still allow a retry to insert twice under unusual isolation. |
| Return `409` for a duplicate | Duplicates are an internal benign race, not a client error; the worker must continue the batch. |

## Consequences

**Easier**

- The worker is safe to restart, to run twice, and to trigger manually.
- Tests can call the service directly and assert idempotency without mocking the scheduler.
- Superintendent queue has a stable one-row-per-complaint contract.

**Harder / constrained**

- Every new escalation write path must go through `escalation_service`; routers may not set `ESCALATED`.
- `GET_LOCK` requires a dedicated connection, not the ORM session that runs candidate transactions.
- `overdue_seconds` must be computed from `resolution_due_at` at escalation time, not from the scheduled run time.

**Forbidden**

- Computing the deadline as `accepted_at + 7 days` in code; always read the configured window and snapshot `sla_seconds`.
- Batch-level transaction wrapping all candidates.
- Silently swallowing a non-duplicate exception; it must be logged with the complaint ID.

## Enforcement

| Check | Where |
|---|---|
| Only `escalation_service` writes `ESCALATED` | Code review + `T-ESC` |
| `UNIQUE(escalations.complaint_id)` present | Migration review, DB-06 |
| Second run returns `evaluated:0, escalated:0` | `T-ESC` idempotency test |
| Resolve-during-run is skipped | `T-ESC` concurrency test |
| Lock contention returns `lock_skipped` | `T-ESC` unit test |
| `IntegrityError` is skipped, not fatal | `T-ESC` integration test |

*End of ADR-001.*
