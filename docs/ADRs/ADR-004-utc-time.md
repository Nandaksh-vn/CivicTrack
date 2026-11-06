# ADR-004 ΓÇö Store UTC, render in `APP_TIMEZONE`

- **Status:** Accepted
- **Date:** 06 November 2026
- **Phase:** 2 (design), implemented in Phase 5
- **Deciders:** Architecture workstream (DOC), backend workstream (BE)
- **References:** FR-027; SRS NFR-018; TRD ┬º5.7, ┬º13.2; ARCHITECTURE ┬º5.4

---

## Context

Escalation correctness depends on comparing `resolution_due_at` with "now" exactly once, consistently, across the API and the worker. The team and demo audience are in India (UTC+05:30), while the database, worker, and tests may run in any container timezone. Mixing local time and UTC produces off-by-hours deadlines, flaky boundary tests, and deadlines that shift when a container's `TZ` changes.

## Decision

**All persisted and compared timestamps are UTC.** Timezone conversion happens only at rendering time.

Rules:

1. `utcnow()` in `app/core/clock.py` returns **naive UTC with microsecond precision** and is the only source of "now" in application code.
2. MySQL columns use `DATETIME(6)`; values are written as UTC. No `TIMESTAMP` columns with implicit server-timezone conversion.
3. `resolution_due_at = accepted_at + sla_seconds` where both sides are UTC.
4. API serialization emits ISO 8601 with a `Z` suffix, e.g. `2026-11-06T10:00:00Z`.
5. `APP_TIMEZONE` (default `UTC`) is a valid IANA zone used only by display/rendering helpers and frontend formatting. It never changes a stored value or a comparison.
6. Tests monkeypatch `utcnow` and cover `deadline ΓêÆ 1 s`, `deadline`, and `deadline + 1 s`.
7. Container `TZ` is irrelevant to correctness; the app must not call `datetime.now()` without a UTC argument anywhere in domain or service code.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Store local time | Deadlines break under DST or container moves; comparisons become ambiguous. |
| Store timezone-aware `DATETIME` per row | MySQL has no native tz-aware type; conversion on read is easy to forget. |
| Use `TIMESTAMP` columns | Implicit server-timezone conversion on read/write is a classic source of drift. |
| Compute in the frontend | The server is authoritative for SLA; client clocks are untrusted. |
| `datetime.now()` with a naive assumption | Explicitly forbidden; depends on process timezone. |

## Consequences

**Easier**

- Deadline math is a single subtraction; no zone lookups in hot paths.
- Boundary tests are deterministic regardless of machine locale.
- Same rule applies to history, audit, and notification timestamps.

**Harder / constrained**

- Every serializer must agree on the `Z` suffix; a shared helper is mandatory.
- Developers must resist `datetime.now()`; a lint/review check enforces `utcnow()`.
- Human-readable reports need explicit `APP_TIMEZONE` rendering.

**Forbidden**

- Writing local time or a server-default timezone into any column.
- Recomputing the deadline from the current configuration after acceptance.
- Letting the browser send a timestamp that is stored as authoritative.

## Enforcement

| Check | Where |
|---|---|
| `utcnow()` is the only now-source | Code review, `T-ESC`, `T-DEPT` |
| API timestamps end in `Z` | Contract tests |
| Boundary tests at ΓêÆ1 s / exact / +1 s | `T-ESC` |
| `APP_TIMEZONE` affects display only | `T-ADMIN` / unit test |
| `sla_seconds` snapshot immutable after accept | `T-DEPT` |

*End of ADR-004.*
