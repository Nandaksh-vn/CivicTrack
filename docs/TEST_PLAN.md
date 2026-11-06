# CivicTrack Test Plan

Maps every test ID to its SRS test group, phase, coverage, and automation
status. This document is the single source of truth for what is tested, how,
and where the evidence lives.

## Conventions

| Field | Meaning |
|-------|---------|
| Test ID | Stable identifier (e.g. `T-AUTH-01`) referenced in test code and UAT report |
| SRS Group | Requirement cluster from `docs/SRS.md` |
| Phase | Delivery phase that owns the test |
| Coverage | FR / AC / BR / NFR / NT requirements exercised |
| Automation | `unit`, `integration`, `e2e`, `manual`, or `skip` |
| Location | File path containing the test |

---

## T-AUTH — Authentication (FR-001..003, FR-005, AC-01)

| Test ID | SRS Group | Phase | Coverage | Automation | Location |
|---------|-----------|-------|----------|------------|----------|
| T-AUTH-01 | Citizen registration | 6/17 | FR-001, AC-01 | integration | `backend/tests/integration/test_auth.py::test_register_citizen_success` |
| T-AUTH-02 | Duplicate email | 6/17 | FR-001 | integration | `test_auth.py::test_register_duplicate_email_conflict` |
| T-AUTH-03 | Password policy | 6/17 | FR-001, NFR-004 | integration | `test_auth.py::test_register_password_policy_validation` |
| T-AUTH-04 | Login success | 6/17 | FR-002 | integration | `test_auth.py::test_login_success` |
| T-AUTH-05 | Invalid password 401 | 6/17 | FR-002 | integration | `test_auth.py::test_login_invalid_password_returns_401` |
| T-AUTH-06 | Nonexistent email 401 | 6/17 | FR-002 | integration | `test_auth.py::test_login_nonexistent_email_returns_401` |
| T-AUTH-07 | Inactive user 401 | 6/17 | FR-002 | integration | `test_auth.py::test_login_inactive_user_returns_identical_401` |
| T-AUTH-08 | Logout 204 | 6/17 | FR-002 | integration | `test_auth.py::test_logout_returns_204` |
| T-AUTH-09 | Get profile | 6/17 | FR-005 | integration | `test_auth.py::test_get_me_success` |
| T-AUTH-10 | Missing token 401 | 6/17 | RBAC-01 | integration | `test_auth.py::test_get_me_unauthorized_without_token` |
| T-AUTH-11 | Expired token | 6/17 | NFR-006 | integration | `test_auth.py::test_expired_token_rejected` |
| T-AUTH-12 | Deactivated user | 6/17 | RBAC-06 | integration | `test_auth.py::test_deactivated_user_token_rejected` |

**Unit:** `tests/unit/test_security.py` (password hashing, JWT, password strength)

---

## T-RBAC — Role-Based Access Control (FR-004, FR-006, AC-14)

| Test ID | SRS Group | Phase | Coverage | Automation | Location |
|---------|-----------|-------|----------|------------|----------|
| T-RBAC-01 | Citizen cannot accept | 12/17 | RBAC-01 | integration | `test_rbac.py::test_rbac_case_1_citizen_cannot_accept` |
| T-RBAC-02 | Citizen cannot reject | 12/17 | RBAC-01 | integration | `test_rbac_case_2_citizen_cannot_reject` |
| T-RBAC-03 | Citizen cannot view department queue | 12/17 | RBAC-01 | integration | `test_rbac_case_3_citizen_cannot_view_department_queue` |
| T-RBAC-04 | Citizen cannot view superintendent escalations | 12/17 | RBAC-01 | integration | `test_rbac_case_4_citizen_cannot_view_superintendent_escalations` |
| T-RBAC-05 | Citizen cannot access admin users | 12/17 | RBAC-01 | integration | `test_rbac_case_5_citizen_cannot_access_admin_users` |
| T-RBAC-06 | Officer cross-department read 403 | 12/17 | RBAC-02 | integration | `test_rbac_case_6_officer_cannot_read_other_department_complaint` |
| T-RBAC-07 | Officer cross-department accept 403 | 12/17 | RBAC-02 | integration | `test_rbac_case_7_officer_cannot_accept_other_department_complaint` |
| T-RBAC-08 | Officer cannot record superintendent action | 12/17 | RBAC-01 | integration | `test_rbac_case_8_officer_cannot_record_superintendent_action` |
| T-RBAC-09 | Superintendent cannot create categories | 12/17 | RBAC-01 | integration | `test_rbac_case_9_superintendent_cannot_create_categories` |
| T-RBAC-10 | Admin cannot accept complaint | 12/17 | RBAC-01 | integration | `test_rbac_case_10_admin_cannot_accept_complaint` |
| T-RBAC-11 | Officer cross-department resolve 403 | 12/17 | RBAC-02 | integration | `test_rbac_case_11_officer_cannot_resolve_other_department_complaint` |
| T-RBAC-12 | Anonymous rejected | 12/17 | RBAC-01 | integration | `test_rbac_case_12_anonymous_rejected` |
| T-RBAC-13 | Denial creates audit log | 12/17 | RBAC-08 | integration | `test_rbac_denial_creates_audit_log` |

**Unit:** `tests/unit/test_deps.py` (object scope guards: complaint owner, officer department, superintendent action)

---

## T-USERS — User Administration (FR-006, T-INT-18)

| Test ID | SRS Group | Phase | Coverage | Automation | Location |
|---------|-----------|-------|----------|------------|----------|
| T-USERS-01 | Admin lists users | 13/17 | FR-006 | integration | `test_rbac.py::test_admin_list_users` |
| T-USERS-02 | Admin creates officer | 13/17 | FR-006 | integration | `test_rbac.py::test_admin_create_officer_with_department` |
| T-USERS-03 | Officer without department fails | 13/17 | FR-006 | integration | `test_rbac.py::test_admin_create_officer_without_department_fails` |
| T-USERS-04 | Last admin protection | 13/17 | FR-006, T-INT-18 | integration | `test_rbac.py::test_last_admin_protection` |
| T-USERS-05 | Concurrent last admin protection | 13/17 | T-INT-18 | integration | `test_rbac.py::test_concurrent_last_admin_protection` |

---

## T-COMPLAINTS — Complaint Lifecycle (FR-015..024, AC-02, AC-04)

| Test ID | SRS Group | Phase | Coverage | Automation | Location |
|---------|-----------|-------|----------|------------|----------|
| T-COMP-01 | Get complaint (owner) | 8/17 | FR-015 | integration | `test_complaints.py::test_get_complaint_owner` |
| T-COMP-02 | Get complaint (foreign citizen 403) | 8/17 | RBAC-03 | integration | `test_complaints.py::test_get_complaint_foreign_citizen_403` |
| T-COMP-03 | Get complaint (officer same dept) | 8/17 | RBAC-02 | integration | `test_complaints.py::test_get_complaint_officer_same_department` |
| T-COMP-04 | Get complaint (officer other dept 403) | 8/17 | RBAC-02 | integration | `test_complaints.py::test_get_complaint_officer_other_department_403` |
| T-COMP-05 | Get complaint not found | 8/17 | FR-015 | integration | `test_complaints.py::test_get_complaint_not_found` |
| T-COMP-06 | Get complaint anonymous 401 | 8/17 | RBAC-01 | integration | `test_complaints.py::test_get_complaint_anonymous_401` |
| T-COMP-07 | Accept complaint (officer) | 12/17 | FR-019 | integration | `test_complaints.py::test_accept_complaint_officer` |
| T-COMP-08 | Accept complaint (citizen 403) | 12/17 | FR-019 | integration | `test_complaints.py::test_accept_complaint_citizen_403` |
| T-COMP-09 | Accept complaint (officer other dept 403) | 12/17 | RBAC-02 | integration | `test_complaints.py::test_accept_complaint_officer_other_dept_403` |
| T-COMP-10 | Reject complaint (officer) | 12/17 | FR-020 | integration | `test_complaints.py::test_reject_complaint_officer` |
| T-COMP-11 | Reject complaint (citizen 403) | 12/17 | FR-020 | integration | `test_complaints.py::test_reject_complaint_citizen_403` |
| T-COMP-12 | Resolve complaint (officer) | 12/17 | FR-024 | integration | `test_complaints.py::test_resolve_complaint_officer` |
| T-COMP-13 | Resolve complaint (superintendent) | 12/17 | FR-041 | integration | `test_complaints.py::test_resolve_complaint_superintendent` |
| T-COMP-14 | Superintendent non-escalated 409 | 12/17 | RBAC-05 | integration | `test_complaints.py::test_resolve_complaint_superintendent_non_escalated_409` |
| T-COMP-15 | Resolve complaint (officer other dept 403) | 12/17 | RBAC-02 | integration | `test_complaints.py::test_resolve_complaint_officer_other_dept_403` |
| T-COMP-16 | Superintendent action | 12/17 | FR-038 | integration | `test_complaints.py::test_superintendent_action` |
| T-COMP-17 | Superintendent action (officer 403) | 12/17 | RBAC-01 | integration | `test_complaints.py::test_superintendent_action_officer_403` |

---

## T-DEPARTMENT — Department Queue (FR-017)

| Test ID | SRS Group | Phase | Coverage | Automation | Location |
|---------|-----------|-------|----------|------------|----------|
| T-DEPT-01 | Department queue (officer) | 12/17 | FR-017 | integration | `test_department_queue.py::test_department_queue_officer` |
| T-DEPT-02 | Department queue (citizen 403) | 12/17 | RBAC-01 | integration | `test_department_queue.py::test_department_queue_citizen_403` |
| T-DEPT-03 | Department queue (anonymous 401) | 12/17 | RBAC-01 | integration | `test_department_queue.py::test_department_queue_anonymous_401` |

---

## T-SUPERINTENDENT — Escalation Queue (FR-035)

| Test ID | SRS Group | Phase | Coverage | Automation | Location |
|---------|-----------|-------|----------|------------|----------|
| T-SUP-01 | Escalations (superintendent) | 12/17 | FR-035 | integration | `test_superintendent_queue.py::test_superintendent_escalations_superintendent` |
| T-SUP-02 | Escalations (officer 403) | 12/17 | RBAC-01 | integration | `test_superintendent_queue.py::test_superintendent_escalations_officer_403` |
| T-SUP-03 | Escalations (citizen 403) | 12/17 | RBAC-01 | integration | `test_superintendent_queue.py::test_superintendent_escalations_citizen_403` |
| T-SUP-04 | Escalations (anonymous 401) | 12/17 | RBAC-01 | integration | `test_superintendent_queue.py::test_superintendent_escalations_anonymous_401` |

---

## T-CONFIG — Configuration Guard (FR-033, AC-16)

| Test ID | SRS Group | Phase | Coverage | Automation | Location |
|---------|-----------|-------|----------|------------|----------|
| T-CONFIG-01 | Default escalation window 7 days | 11/17 | FR-033 | unit | `test_config.py::test_default_escalation_window_is_seven_days` |
| T-CONFIG-02 | Non-default reverted without demo flag | 11/17 | FR-033 | unit | `test_config.py::test_non_default_window_is_reverted_without_demo_flag` |
| T-CONFIG-03 | Non-default kept with demo flag | 11/17 | FR-033 | unit | `test_config.py::test_non_default_window_is_kept_with_demo_flag` |
| T-CONFIG-04 | CORS origins split/trimmed | 14/17 | NFR-021 | unit | `test_config.py::test_cors_origins_are_split_and_trimmed` |
| T-CONFIG-05 | Compatibility aliases from env | 14/17 | NFR-021 | unit | `test_config.py::test_compatibility_aliases_are_read_from_environment` |
| T-CONFIG-06 | Production rejects placeholder secrets | 18/17 | NFR-022 | unit | `test_config.py::test_production_rejects_placeholder_secrets` |
| T-CONFIG-07 | Production accepts safe configuration | 18/17 | NFR-022 | unit | `test_config.py::test_production_accepts_safe_configuration` |

---

## T-SCHEMA — Schema Validation (FR-001, FR-002, FR-006)

| Test ID | SRS Group | Phase | Coverage | Automation | Location |
|---------|-----------|-------|----------|------------|----------|
| T-SCHEMA-01 | Register request valid | 6/17 | FR-001 | unit | `test_schemas.py::test_register_request_valid` |
| T-SCHEMA-02 | Register request rejects invalid | 6/17 | FR-001 | unit | `test_schemas.py::test_register_request_rejects_invalid` |
| T-SCHEMA-03 | Login request valid | 6/17 | FR-002 | unit | `test_schemas.py::test_login_request_valid` |
| T-SCHEMA-04 | Login request rejects invalid | 6/17 | FR-002 | unit | `test_schemas.py::test_login_request_rejects_invalid` |
| T-SCHEMA-05 | Admin user create (citizen) | 13/17 | FR-006 | unit | `test_schemas.py::test_admin_user_create_valid_citizen` |
| T-SCHEMA-06 | Admin user create (officer) | 13/17 | FR-006 | unit | `test_schemas.py::test_admin_user_create_valid_officer` |
| T-SCHEMA-07 | Admin user update partial | 13/17 | FR-006 | unit | `test_schemas.py::test_admin_user_update_partial` |
| T-SCHEMA-08 | Public user excludes password | 6/17 | NFR-022 | unit | `test_schemas.py::test_public_user_excludes_password` |
| T-SCHEMA-09 | DepartmentOut valid | 13/17 | FR-046 | unit | `test_schemas.py::test_department_out_valid` |

---

## T-SECURITY — Security Utilities (NFR-004, NFR-006)

| Test ID | SRS Group | Phase | Coverage | Automation | Location |
|---------|-----------|-------|----------|------------|----------|
| T-SEC-01 | Password strength accepts valid | 6/17 | NFR-004 | unit | `test_security.py::test_validate_password_strength_accepts_valid` |
| T-SEC-02 | Password strength rejects invalid | 6/17 | NFR-004 | unit | `test_security.py::test_validate_password_strength_rejects_invalid` |
| T-SEC-03 | Hash password bcrypt cost 12 | 6/17 | NFR-004 | unit | `test_security.py::test_hash_password_uses_bcrypt_cost_12` |
| T-SEC-04 | Verify password matching | 6/17 | NFR-004 | unit | `test_security.py::test_verify_password_matching` |
| T-SEC-05 | Verify password nonmatching | 6/17 | NFR-004 | unit | `test_security.py::test_verify_password_nonmatching` |
| T-SEC-06 | Verify malformed hash | 6/17 | NFR-004 | unit | `test_security.py::test_verify_password_malformed_hash` |
| T-SEC-07 | JWT round trip | 6/17 | NFR-006 | unit | `test_security.py::test_create_access_token_round_trip` |
| T-SEC-08 | JWT with department | 6/17 | NFR-006 | unit | `test_security.py::test_create_access_token_with_department` |
| T-SEC-09 | JWT custom expiry | 6/17 | NFR-006 | unit | `test_security.py::test_create_access_token_custom_expiry` |
| T-SEC-10 | Expired token rejected | 6/17 | NFR-006 | unit | `test_security.py::test_decode_expired_token_raises` |
| T-SEC-11 | Tampered token rejected | 6/17 | NFR-006 | unit | `test_security.py::test_decode_tampered_token_raises` |
| T-SEC-12 | Bcrypt rounds >= 12 | 6/17 | NFR-004 | unit | `test_security.py::test_bcrypt_rounds_meets_minimum` |

---

## T-ENUM — Canonical Enums (TRD §3.1, §3.2, §7)

| Test ID | SRS Group | Phase | Coverage | Automation | Location |
|---------|-----------|-------|----------|------------|----------|
| T-ENUM-01 | Role values | 6/17 | TRD §3.1 | unit | `test_enums.py::test_role_values` |
| T-ENUM-02 | Status values | 6/17 | TRD §3.1 | unit | `test_enums.py::test_status_values` |
| T-ENUM-03 | Priority values | 6/17 | TRD §3.1 | unit | `test_enums.py::test_priority_values` |
| T-ENUM-04 | ImageKind values | 6/17 | TRD §7 | unit | `test_enums.py::test_image_kind_values` |
| T-ENUM-05 | CommentType/Visibility | 6/17 | TRD §7 | unit | `test_enums.py::test_comment_type_values` |
| T-ENUM-06 | OfficerActionType values | 6/17 | TRD §7 | unit | `test_enums.py::test_officer_action_type_values` |
| T-ENUM-07 | TriggerSource values | 11/17 | TRD §7 | unit | `test_enums.py::test_trigger_source_values` |

---

## T-E2E — Playwright End-to-End (US-E2E-01, AC-01..AC-16)

| Test ID | SRS Group | Phase | Coverage | Automation | Location |
|---------|-----------|-------|----------|------------|----------|
| T-E2E-01 | Citizen register → login → workspace | 16/17 | AC-01 | e2e | `frontend/tests/e2e/golden-path.spec.ts` |
| T-E2E-02 | Citizen log out → log back in | 16/17 | AC-01 | e2e | `frontend/tests/e2e/golden-path.spec.ts` |
| T-E2E-03 | Citizen blocked from superintendent route | 16/17 | AC-14 | e2e | `frontend/tests/e2e/golden-path.spec.ts` |
| T-E2E-04 | Citizen blocked from admin route | 16/17 | AC-14 | e2e | `frontend/tests/e2e/golden-path.spec.ts` |
| T-E2E-05 | Anonymous redirected to login | 16/17 | RBAC-01 | e2e | `frontend/tests/e2e/golden-path.spec.ts` |
| T-E2E-06 | Repeated escalation → one record | 11/17 | AC-08 | e2e | `frontend/tests/e2e/golden-path.spec.ts` (skip until wired) |
| T-E2E-07 | Axe scan: landing | 18/17 | NFR-014 | e2e | `frontend/tests/e2e/accessibility.spec.ts` |
| T-E2E-08 | Axe scan: login | 18/17 | NFR-014 | e2e | `frontend/tests/e2e/accessibility.spec.ts` |
| T-E2E-09 | Axe scan: register | 18/17 | NFR-014 | e2e | `frontend/tests/e2e/accessibility.spec.ts` |
| T-E2E-10 | Axe scan: My Complaints (auth) | 18/17 | NFR-014 | e2e | `frontend/tests/e2e/accessibility.spec.ts` |
| T-E2E-11 | Keyboard: landing page | 18/17 | NFR-015 | e2e | `frontend/tests/e2e/accessibility.spec.ts` |
| T-E2E-12 | Keyboard: register form | 18/17 | NFR-015 | e2e | `frontend/tests/e2e/accessibility.spec.ts` |

---

## T-FRONTEND — Frontend Component Tests (TEST-041)

| Test ID | SRS Group | Phase | Coverage | Automation | Location |
|---------|-----------|-------|----------|------------|----------|
| T-FE-01 | StatusBadge renders all statuses | 14/17 | TRD §3.1 | unit | `frontend/tests/unit/StatusBadge.test.tsx` |
| T-FE-02 | StatusBadge unknown status passthrough | 14/17 | TRD §3.1 | unit | `frontend/tests/unit/StatusBadge.test.tsx` |
| T-FE-03 | FormField renders label + children | 14/17 | NFR-015 | unit | `frontend/tests/unit/FormField.test.tsx` |
| T-FE-04 | FormField renders hint | 14/17 | NFR-015 | unit | `frontend/tests/unit/FormField.test.tsx` |
| T-FE-05 | FormField renders error alert | 14/17 | NFR-015 | unit | `frontend/tests/unit/FormField.test.tsx` |
| T-FE-06 | FormField no error when absent | 14/17 | NFR-015 | unit | `frontend/tests/unit/FormField.test.tsx` |
| T-FE-07 | ProtectedRoute loading state | 14/17 | NFR-010 | unit | `frontend/tests/unit/ProtectedRoute.test.tsx` |
| T-FE-08 | ProtectedRoute redirects unauthenticated | 14/17 | RBAC-01 | unit | `frontend/tests/unit/ProtectedRoute.test.tsx` |
| T-FE-09 | ProtectedRoute allows allowed role | 14/17 | RBAC-01 | unit | `frontend/tests/unit/ProtectedRoute.test.tsx` |
| T-FE-10 | ProtectedRoute forbidden for wrong role | 14/17 | RBAC-01 | unit | `frontend/tests/unit/ProtectedRoute.test.tsx` |
| T-FE-11 | LoginPage renders fields | 14/17 | AC-01 | unit | `frontend/tests/unit/LoginPage.test.tsx` |
| T-FE-12 | LoginPage shows server error | 14/17 | AC-01 | unit | `frontend/tests/unit/LoginPage.test.tsx` |
| T-FE-13 | RegisterPage renders fields | 14/17 | AC-01 | unit | `frontend/tests/unit/RegisterPage.test.tsx` |
| T-FE-14 | RegisterPage duplicate email field error | 14/17 | AC-01 | unit | `frontend/tests/unit/RegisterPage.test.tsx` |
| T-FE-15 | RegisterPage generic server error | 14/17 | AC-01 | unit | `frontend/tests/unit/RegisterPage.test.tsx` |
| T-FE-16 | AppRoutes redirects to login | 14/17 | RBAC-01 | unit | `frontend/tests/unit/AppRoutes.test.tsx` |
| T-FE-17 | AppRoutes not-found page | 14/17 | NFR-010 | unit | `frontend/tests/unit/AppRoutes.test.tsx` |

---

## Coverage Summary

| Category | Requirement IDs | Tests | Status |
|----------|----------------|-------|--------|
| Authentication | FR-001..003, FR-005, AC-01 | 12 integration + 4 unit | ✅ Complete |
| RBAC | FR-004, FR-006, AC-14, RBAC-01..08 | 13 integration + 3 unit | ✅ Complete |
| User Administration | FR-006, T-INT-18 | 5 integration | ✅ Complete |
| Complaint Lifecycle | FR-015..024, AC-02, AC-04 | 17 integration | ✅ Complete |
| Department Queue | FR-017 | 3 integration | ✅ Complete |
| Superintendent Queue | FR-035 | 4 integration | ✅ Complete |
| Config Guard | FR-033, AC-16 | 7 unit | ✅ Complete |
| Schema Validation | FR-001, FR-002, FR-006 | 9 unit | ✅ Complete |
| Security | NFR-004, NFR-006 | 12 unit | ✅ Complete |
| Enums | TRD §3.1, §7 | 7 unit | ✅ Complete |
| Frontend Components | NFR-010, NFR-014, NFR-015 | 17 unit | ✅ Complete |
| E2E Golden Path | US-E2E-01, AC-01..16 | 6 e2e | ⚠️ Partial (backend wiring pending) |
| Accessibility | NFR-014, NFR-015 | 6 e2e | ⚠️ Partial (requires running servers) |

**Gap notes:**
- `T-E2E-06` (idempotency) is skipped until the escalation worker and `POST /internal/escalations/run` are wired to the frontend (INT-010).
- Full golden-path lifecycle (submit → accept → progress → escalate → resolve → citizen verifies) requires complaint creation and escalation endpoints to be wired (Phases 15-16).
