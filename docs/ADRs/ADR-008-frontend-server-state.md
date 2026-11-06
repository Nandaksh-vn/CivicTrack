# ADR-008 ΓÇö TanStack Query owns server state; one status map for presentation

- **Status:** Accepted
- **Date:** 06 November 2026
- **Phase:** 2 (design), implemented in Phase 4/7
- **Deciders:** Architecture workstream (DOC), frontend workstream (FE)
- **References:** FR-004, FR-014, FR-015, FR-043, FR-044; SRS NFR-016; TRD ┬º4.3ΓÇô┬º4.8; ARCHITECTURE ┬º8

---

## Context

The SPA has four role homes, several list/detail screens, and mutations that change data other screens display. P0 has no websocket or SSE; notifications are polled. Two recurring defects in this shape are (a) duplicating server data into a client store and letting it drift, and (b) mapping statuses to colors/labels in multiple components, so `ESCALATED` looks different on two pages.

Role changes and deactivation must take effect immediately server-side, so the client must not cache identity beyond a reload.

## Decision

**TanStack Query is the single owner of server state. Redux/Zustand-style global stores are not used in P0. All status presentation comes from one module.**

Rules:

1. Server data lives only in the TanStack Query cache. React component state is limited to UI concerns (open/closed, form draft).
2. Auth state is an exception: the token lives in `sessionStorage`; the current user is held in `AuthProvider` memory and refetched via `GET /auth/me` on reload. Role is read from that response, never from a decoded token.
3. Forms are owned by `react-hook-form` with Zod schemas that mirror server constraints.
4. Query keys are fixed and shared from `src/lib/queryKeys.ts`: `['me']`, `['complaints', filters]`, `['complaint', id]`, `['timeline', id]`, `['department', filters]`, `['department-summary']`, `['escalations']`, `['notifications']`, `['unread-count']`, `['admin', resource]`.
5. Every mutation declares its invalidation set (ARCHITECTURE ┬º8.3). A mutation that changes a complaint invalidates detail, timeline, the relevant list, and `['unread-count']`.
6. No optimistic status change. The UI shows a pending state, waits for the server, then invalidates. A `409` refreshes the complaint and shows a conflict banner.
7. Notifications poll `GET /notifications/unread-count` every 30 s while the tab is visible and on focus. The full list is fetched on demand.
8. `src/lib/status.ts` is the only place that maps a status to a label and badge style. Components import from it; no inline status switch.
9. Route guards are UX only. They redirect using the role from `GET /auth/me`, and every API call still relies on server authorization.
10. P1 features (`AiSuggest`, `IssueMap`, `Analytics`, feedback/reopen) are lazy-loaded behind `VITE_ENABLE_*` flags and must not be imported by P0 modules.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Redux Toolkit / Zustand for everything | Duplicates server state and requires manual cache sync; more code for the same result. |
| `useEffect` + `useState` fetching | No shared cache, no invalidation, refetch storms, and inconsistent loading states. |
| Store the JWT in a global store | `sessionStorage` is the chosen persistence; a store adds a second source of truth. |
| Websocket/SSE for notifications | Out of P0 scope; polling every 30 s is sufficient and simpler to operate. |
| Per-component status color maps | Guarantees divergence between screens. |
| Optimistic status mutation | The server is authoritative for transitions; optimistic UI would show illegal states on `409`. |

## Consequences

**Easier**

- One cache, one invalidation model, consistent loading/error states.
- Status labels and colors are provably identical across all screens.
- Role changes apply on reload without stale client identity.

**Harder / constrained**

- Every mutation must declare its invalidation set; forgetting one causes stale UI.
- Cache keys must be stable and serializable; filter objects need deterministic ordering.
- The 30 s poll is a deliberate staleness window; read-marking must invalidate immediately.

**Forbidden**

- Copying query data into component or global state as a second source of truth.
- Decoding the JWT on the client to decide a role.
- A second status-to-label map.
- Importing P1 modules into P0 route chunks.

## Enforcement

| Check | Where |
|---|---|
| Every mutation invalidates documented keys | FE review, `T-E2E` |
| `status.ts` is the only status map | grep + review |
| `409` shows conflict and refetches | `T-DEPT` / FE test |
| Poll pauses when the tab is hidden | FE test |
| P1 code not in P0 bundle | build/bundle check |
| Role guard uses `/auth/me` | `T-RBAC` / `T-E2E` |

*End of ADR-008.*
