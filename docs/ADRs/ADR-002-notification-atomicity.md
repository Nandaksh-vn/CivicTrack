# ADR-002 ΓÇö Notifications commit with the transition

- **Status:** Accepted
- **Date:** 06 November 2026
- **Phase:** 2 (design), implemented in Phase 8
- **Deciders:** Architecture workstream (DOC), backend workstream (BE)
- **References:** FR-042, FR-045; SRS NT-01ΓÇªNT-07; TRD ┬º11.3; ARCHITECTURE ┬º5.2, ┬º6.2

---

## Context

Every citizen-visible state change must notify the right actors. If a notification is written after the business transaction commits, a crash in between leaves a transition with no notification ΓÇö the citizen sees a status change they were never told about. If the notification is sent outside the database entirely (email, push), the system has no durable record and the test suite cannot assert delivery.

P0 has no email, SMS, or push channel. Notifications are in-app rows read by polling.

## Decision

**Notification rows are written inside the same database transaction as the state change that triggers them.** There is no post-commit hook, no background queue, and no outbox table in P0.

Rules:

1. The service performing the transition calls `notification_service` **before** `COMMIT`, passing the same session.
2. If notification creation raises, the whole transition rolls back; the client receives the error and the complaint keeps its previous status.
3. Recipient resolution is part of the notification service, not the caller:
   - NT-01 submission ΓåÆ officers of the mapped department.
   - NT-02 accept ΓåÆ complaint owner.
   - NT-03 reject ΓåÆ complaint owner.
   - NT-04 progress ΓåÆ complaint owner.
   - NT-05 escalation ΓåÆ active Superintendents, active officers of the responsible department, and the citizen.
   - NT-06 superintendent action ΓåÆ responsible department officers and the citizen.
   - NT-07 resolve ΓåÆ complaint owner.
4. Notification `title`/`body` are plain text, contain the tracking number and the resulting status, and contain no password, token, or internal identifier.
5. Notifications are append-only through the API: clients may mark read but never create, edit, or delete.
6. The escalation worker applies the same rule per candidate; a notification failure rolls back only that candidate.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Transactional outbox + relay worker | Correct at scale but adds a table, a poller, and retry semantics the P0 scope does not need. |
| Post-commit best-effort insert | Silent loss window; violates the "every transition notifies" requirement. |
| Fire-and-forget thread/task | Untestable, non-deterministic, and can outlive the request transaction. |
| External email/SMS in P0 | Explicitly out of scope; no provider, no credentials, no delivery guarantee. |
| Notification service opening its own session | Breaks atomicity and can deadlock against the transition's row lock. |

## Consequences

**Easier**

- A committed status change always has its notifications.
- Tests assert counts and recipients in the same assertion block as the status.
- No retry or dead-letter infrastructure to operate.

**Harder / constrained**

- Transition latency includes notification insert cost; recipient queries must be indexed (`users.role`, `users.department_id`, `users.is_active`).
- A notification bug blocks the business action; this is intentional and must be caught in Phase 8 tests.
- Notification volume is bounded by transition volume, so no batching in P0.

**Forbidden**

- Calling `notification_service` after `COMMIT`.
- Sending a notification for a transition that later rolls back.
- Putting PII beyond the minimum display fields into `body`.

## Enforcement

| Check | Where |
|---|---|
| Notification insert shares the transition session | Code review, `T-NOTIF` |
| Rolled-back transition leaves zero notifications | `T-NOTIF` integration test |
| Each trigger code reaches the documented recipients | `T-NOTIF` matrix test |
| No duplicate notification on retry of an idempotent read-mark | `T-NOTIF` |
| Escalation notification failure isolates to one candidate | `T-ESC` |

*End of ADR-002.*
