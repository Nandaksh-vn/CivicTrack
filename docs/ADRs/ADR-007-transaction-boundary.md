# ADR-007 ΓÇö Service-owned transactions on `READ COMMITTED`

- **Status:** Accepted
- **Date:** 06 November 2026
- **Phase:** 2 (design), implemented in Phase 5 (`BE-008`)
- **Deciders:** Architecture workstream (DOC), backend workstream (BE)
- **References:** NFR-012; SRS DB-09, BR-14; TRD ┬º5.2ΓÇô┬º5.3, ┬º13.5; ARCHITECTURE ┬º5.2

---

## Context

A complaint transition touches several tables in one logical step: `complaints`, `complaint_status_history`, `notifications`, sometimes `escalations`, `complaint_images`, or `officer_actions`. Partial commits corrupt the timeline and can leave a status without its notification. At the same time, long-running transactions cause lock contention, and MySQL's default `REPEATABLE READ` produces gap locks that interfere with the escalation candidate query.

## Decision

**One unit of work per command request, owned by the service, on `READ COMMITTED` isolation. Routers never commit.**

Rules:

1. `get_db` yields a session and closes it in `finally`; it does not commit or roll back business work.
2. Command services wrap work in `with db.begin():`. Success commits once; any exception rolls back the whole unit.
3. State transitions lock the target row with `SELECT ... FOR UPDATE` **before** the guard, so two actors cannot both pass the same guard.
4. All side effects of a transition ΓÇö history row, notification rows, escalation row, image metadata ΓÇö are written inside the same transaction (ADR-002).
5. Read endpoints use SQLAlchemy autobegin and never commit.
6. The escalation worker opens **one session/transaction per candidate**, not one for the batch.
7. Isolation is `READ COMMITTED`. Correctness relies on explicit row locks and conditional updates, not on snapshot isolation.
8. Uploaded files use temp-write-plus-atomic-move and are removed in `finally` when the transaction fails.
9. Repositories do not call `commit()`; only the service boundary does.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Autocommit per statement | No atomicity across the transition's tables. |
| Router-level transaction middleware | Hides the boundary, makes read/write split awkward, and encourages commits in routers. |
| `REPEATABLE READ` (MySQL default) | Gap locks in the candidate query and stale snapshots under concurrent transitions. |
| `SERIALIZABLE` | Overkill; increases deadlock and retry handling for no correctness gain given row locks. |
| Batch transaction for escalation | One bad candidate rolls back the whole run. |
| Repository-owned commits | Scattered transaction boundaries and hard-to-test invariants. |

## Consequences

**Easier**

- Every transition is all-or-nothing and testable by forcing an exception mid-service.
- Test fixtures can wrap each test in a transaction and roll back for isolation.
- Deadlock surface is small because locks are taken in a consistent order (complaint row first).

**Harder / constrained**

- Services must be explicit about `begin()`; a stray `commit()` in a repository is a review defect.
- Long notification recipient queries extend the row-lock hold time; they must use indexes.
- Retry-on-deadlock is not automatic in P0; the API returns a conflict/error and the client retries manually.

**Forbidden**

- `db.commit()` in a router or repository.
- Holding a transaction open across an external network call (image validation is local; P1 external calls are outside the transaction).
- Relying on isolation level alone instead of `FOR UPDATE` for transition guards.

## Enforcement

| Check | Where |
|---|---|
| Forced exception mid-service leaves no partial rows | `T-DEPT` / `T-COMP` rollback test (Phase 5 `BE-021`) |
| Two concurrent accepts: one `200`, one `409` | `T-DEPT` concurrency test |
| Notification and history absent when transition rolls back | `T-NOTIF` |
| Per-test DB isolation via rollback | `conftest.py` (Phase 5 `BE-018`) |
| No `commit()` outside services | Code review + grep check |

*End of ADR-007.*
