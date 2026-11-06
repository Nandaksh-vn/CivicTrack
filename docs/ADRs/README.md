# Architecture Decision Records (ADRs)

> **Document type:** Phase 2 deliverable ΓÇö decision log  
> **Status:** Approved  
> **Date:** 06 November 2026  
> **Companion:** [`../ARCHITECTURE.md`](../ARCHITECTURE.md), [`../API_CONTRACT.md`](../API_CONTRACT.md), [`../STATE_MACHINE.md`](../STATE_MACHINE.md)

---

## 1. Purpose

An ADR records **one** architectural decision: the context that forced a choice, the decision itself, the alternatives rejected, and the consequences. ADRs are immutable once accepted. A later reversal is a **new** ADR that supersedes the old one; the old file stays in place with a `Superseded by` line.

Phase 2 publishes ADR-001ΓÇªADR-008. Every decision here is binding for Phases 3ΓÇô13.

## 2. Format

| Section | Meaning |
|---|---|
| Status | `Accepted`, `Superseded`, or `Deprecated` |
| Context | The constraint or risk that made a decision necessary |
| Decision | What was chosen, stated as an imperative |
| Alternatives considered | Options rejected and why |
| Consequences | What becomes easier, harder, or forbidden |
| Enforcement | Where the rule is checked (code, test, review) |
| References | Source requirement and design section |

## 3. Index

| ADR | Title | Primary requirement |
|---|---|---|
| [ADR-001](./ADR-001-escalation-idempotency.md) | Exactly-once escalation under concurrency | FR-028, FR-029, ESC-01ΓÇªESC-12 |
| [ADR-002](./ADR-002-notification-atomicity.md) | Notifications commit with the transition | FR-042, FR-045, NT-01ΓÇªNT-07 |
| [ADR-003](./ADR-003-upload-storage.md) | Local volume storage with authorized streaming | FR-010, FR-023, SEC-09 |
| [ADR-004](./ADR-004-utc-time.md) | Store UTC, render in `APP_TIMEZONE` | FR-027, NFR-018 |
| [ADR-005](./ADR-005-demo-escalation-guard.md) | Production window by default, explicit demo guard | FR-033, ESC-11 |
| [ADR-006](./ADR-006-jwt-session-storage.md) | Stateless JWT in `sessionStorage`, DB role authority | FR-002, FR-004, SEC-02 |
| [ADR-007](./ADR-007-transaction-boundary.md) | Service-owned transactions, `READ COMMITTED` | NFR-012, DB-09 |
| [ADR-008](./ADR-008-frontend-server-state.md) | TanStack Query owns server state; one status map | FR-004, NFR-016 |

## 4. Change process

1. Propose the ADR with status `Proposed`.
2. Design review checks it does not contradict a frozen requirement or an accepted ADR.
3. On approval set `Accepted`, add it to this index, and update [`../ARCHITECTURE.md`](../ARCHITECTURE.md) if the system shape changes.
4. Add a matching tracker task for any implementation work the decision creates.
5. Never edit an accepted ADR's decision text; supersede it.

## 5. Traceability

| ADR | Tracker task | Design section |
|---|---|---|
| ADR-001 | DOC-016, DOC-021 | ARCHITECTURE ┬º6 |
| ADR-002 | DOC-021 | ARCHITECTURE ┬º5.2, ┬º6.2 |
| ADR-003 | DOC-021 | ARCHITECTURE ┬º4.2 |
| ADR-004 | DOC-021 | ARCHITECTURE ┬º5.4 |
| ADR-005 | DOC-021, BE-005 | ARCHITECTURE ┬º5.3 |
| ADR-006 | DOC-017, DOC-021 | ARCHITECTURE ┬º7 |
| ADR-007 | DOC-021, BE-008 | ARCHITECTURE ┬º5.2 |
| ADR-008 | DOC-018, DOC-021 | ARCHITECTURE ┬º8 |

*End of ADR index ΓÇö Phase 2, CivicTrack.*
