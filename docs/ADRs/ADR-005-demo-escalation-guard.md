# ADR-005 ΓÇö Production escalation window by default, explicit demo guard

- **Status:** Accepted
- **Date:** 06 November 2026
- **Phase:** 2 (design), validated in Phase 5 (`BE-005`)
- **Deciders:** Architecture workstream (DOC), backend workstream (BE)
- **References:** FR-033; SRS ESC-11; TRD ┬º13.7; ARCHITECTURE ┬º5.3

---

## Context

The product requirement is a **seven-day** escalation window (10,080 minutes / 604,800 seconds). A live demo cannot wait seven days, so operators need a shorter window. That convenience is dangerous: an environment variable left short in production would escalate every complaint almost immediately and destroy the SLA's meaning.

The configuration must be safe by default and visible when it is not.

## Decision

**The production window is the default and a shorter window requires an explicit, loudly-logged opt-in.**

Rules:

1. `ESCALATION_WINDOW_MINUTES` defaults to `10080`. Valid range `1ΓÇª525600`; out of range refuses startup.
2. `ALLOW_DEMO_ESCALATION` defaults to `false`.
3. At startup, if the window Γëá `10080` **and** the guard is `false`:
   - log `ESCALATION_WINDOW_OVERRIDE_BLOCKED` at warning level,
   - force the effective window to `10080`,
   - continue running.
4. If the guard is `true`, log `DEMO_ESCALATION_MODE` prominently with the effective window.
5. Every acceptance snapshots `sla_seconds` from the **effective** window, so the value is visible in the data, the API, and the UI.
6. `GET /internal/escalation-status` and `GET /admin/activity` expose `effective_window_minutes` and `demo_mode` for transparency.
7. The deadline is always `accepted_at + sla_seconds`; code never hardcodes seven days.

The same pattern applies to the other interval settings: `ESCALATION_CHECK_SECONDS` (default `60`, range `5ΓÇª3600`) and `ESCALATION_BATCH_SIZE` (default `100`, range `1ΓÇª1000`) refuse startup when out of range.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Allow any window without a guard | A single env typo silently breaks the SLA in production. |
| Refuse startup when the window Γëá `10080` | Blocks legitimate demo and test environments entirely. |
| Separate demo build/branch | Divergence risk; the demo path would not exercise production code. |
| Compute the deadline from configuration at read time | Existing complaints would change deadline after a config edit. |
| Hardcode seven days and patch for demo | Explicitly violates the requirement and hides the value from data. |

## Consequences

**Easier**

- Production is safe with zero extra configuration.
- Demo mode is one flag and is visible in logs, status, and admin activity.
- Existing deadlines are immutable; configuration changes affect only new acceptances.

**Harder / constrained**

- Tests for the override path must assert the forced window and the log event.
- The admin UI must render `demo_mode` so the audience knows the window is shortened.

**Forbidden**

- `accepted_at + timedelta(days=7)` anywhere in code.
- Starting with an out-of-range window or interval instead of failing fast.
- Silently using a short window without the guard flag.

## Enforcement

| Check | Where |
|---|---|
| Invalid window refuses startup | `T-ESC` config test (Phase 5 `BE-005`) |
| Short window without guard is forced to `10080` | `T-ESC` startup test |
| Guard true logs `DEMO_ESCALATION_MODE` | Log assertion test |
| `sla_seconds` snapshot persists per acceptance | `T-DEPT` |
| Admin activity exposes window + demo flag | `T-ADMIN`, `T-ESC` |

*End of ADR-005.*
