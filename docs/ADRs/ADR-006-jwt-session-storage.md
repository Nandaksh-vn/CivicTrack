# ADR-006 ΓÇö Stateless JWT in `sessionStorage`, database role is authoritative

- **Status:** Accepted
- **Date:** 06 November 2026
- **Phase:** 2 (design), implemented in Phase 6/7
- **Deciders:** Architecture workstream (DOC), backend workstream (BE)
- **References:** FR-002, FR-004, FR-005; SRS SEC-01ΓÇªSEC-08, RBAC-01ΓÇªRBAC-08; TRD ┬º9; ARCHITECTURE ┬º7

---

## Context

The app has four roles and object-scope rules (own complaint, own department, escalated-only). It is a browser SPA served from the same origin in Compose but from a different origin in the hosted variant. The team needs immediate effect when an Administrator deactivates a user or changes a role, without building a token denylist. CSRF and XSS are both realistic threats.

## Decision

**Authentication uses a short-lived HS256 JWT carried in the `Authorization` header and stored in `sessionStorage`. Authorization always re-reads the user from the database.**

Rules:

1. Claims: `sub` (user ID string), `role`, `dept`, `iat`, `exp = iat + 8 h`, `jti`, `iss=civictrack`, `aud=civictrack-web`.
2. Secret from `JWT_SECRET`, minimum 32 bytes; missing/invalid refuses startup.
3. Token stored in `sessionStorage` under `civictrack.token`; sent as `Authorization: Bearer <jwt>`. No cookies, so no CSRF surface and `allow_credentials=false`.
4. On every request the API loads the user by `sub`; the **database** role and active flag decide authorization, not the token's `role` claim. Deactivation or role change takes effect on the next request.
5. Authorization has four layers: route role gate ΓåÆ object scope in the service ΓåÆ state guard ΓåÆ frontend route guard (UX only).
6. Status mapping: missing/expired/invalid token or inactive user ΓåÆ `401 TOKEN_INVALID`; wrong role or wrong department ΓåÆ `403 FORBIDDEN`; absent resource or citizen scope violation ΓåÆ `404 NOT_FOUND`; illegal transition ΓåÆ `409 INVALID_TRANSITION`.
7. Login is rate-limited to 5 failures per `(ip, email)` per 60 s ΓåÆ `429 RATE_LIMITED` with `Retry-After`; success resets.
8. Passwords are bcrypt cost 12; password fields are never logged or returned.
9. Logout is client-side disposal plus a `POST /auth/logout` acknowledgement; server-side revocation via `jti` denylist is out of scope for P0.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| `localStorage` | Survives tab close; longer exposure window for a stolen token. |
| HttpOnly cookie | Requires CSRF protection and complicates the cross-origin hosted variant. |
| Trust the `role` claim in the JWT | Role changes and deactivation would not take effect until expiry. |
| Opaque server-side sessions | Needs a session store and revocation table beyond P0 scope. |
| Refresh tokens | Adds rotation, reuse detection, and storage complexity not required for an 8-hour session. |
| Long-lived tokens | Increases blast radius; 8 h matches a working day. |

## Consequences

**Easier**

- Immediate effect for deactivation and role changes.
- No CSRF handling; simple CORS allowlist.
- Token tampering fails signature verification; a forged `role` claim is ignored anyway.

**Harder / constrained**

- Every authenticated request performs a user lookup; the primary key lookup must stay cheap.
- A stolen token is valid for up to 8 hours; there is no server-side kill switch in P0 beyond deactivation.
- `sessionStorage` is per-tab, so a new tab requires login again.

**Forbidden**

- Returning `password_hash` or any password field in any response.
- Logging tokens, passwords, emails, or phones.
- Using the JWT `role`/`dept` claims as the authorization source.
- `allow_credentials=true` with a wildcard origin.

## Enforcement

| Check | Where |
|---|---|
| Forged `role` claim does not grant access | `T-RBAC` |
| Deactivated user gets `401` on the next request | `T-AUTH`, `T-RBAC` |
| Cross-department action returns `403` | `T-RBAC` |
| Citizen reading another complaint returns `404` | `T-RBAC` |
| Six failed logins trigger `429` with `Retry-After` | `T-AUTH` |
| Token/password never appear in logs | log-redaction test (Phase 5 `BE-021`) |

*End of ADR-006.*
