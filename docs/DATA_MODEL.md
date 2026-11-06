# CivicTrack — Relational Data Model & Schema Specification

> **Document:** `docs/DATA_MODEL.md`  
> **Target Release:** v1.0.0-p0  
> **Status:** Final Baseline  
> **Source Documents:** `docs/TRD.md` (§7), `docs/SRS.md`  

---

## 1. Entity-Relationship Diagram

```mermaid
erDiagram
    DEPARTMENTS ||--o{ USERS : "employs"
    DEPARTMENTS ||--o{ COMPLAINT_CATEGORIES : "owns"
    DEPARTMENTS ||--o{ COMPLAINTS : "handles"
    USERS ||--o{ COMPLAINTS : "files"
    USERS ||--o{ NOTIFICATIONS : "receives"
    USERS ||--o{ AUDIT_LOGS : "acts"
    COMPLAINT_CATEGORIES ||--o{ COMPLAINTS : "classifies"
    COMPLAINTS ||--o{ COMPLAINT_IMAGES : "contains"
    COMPLAINTS ||--o{ COMPLAINT_STATUS_HISTORY : "tracks"
    COMPLAINTS ||--o{ COMPLAINT_COMMENTS : "notes"
    COMPLAINTS ||--o{ NOTIFICATIONS : "generates"
    COMPLAINTS ||--o| ESCALATIONS : "breaches"
    COMPLAINTS ||--o{ OFFICER_ACTIONS : "directs"

    USERS {
        int id PK
        string email UK
        string password_hash
        string full_name
        string phone
        string role
        int department_id FK
        bool is_active
        datetime created_at
        datetime updated_at
    }

    DEPARTMENTS {
        int id PK
        string name UK
        string code UK
        string description
        bool is_active
        datetime created_at
        datetime updated_at
    }

    COMPLAINT_CATEGORIES {
        int id PK
        string name UK
        string code UK
        int department_id FK
        string default_priority
        bool is_active
        datetime created_at
        datetime updated_at
    }

    COMPLAINTS {
        int id PK
        string complaint_number UK
        int citizen_id FK
        int category_id FK
        int department_id FK
        string title
        text description
        string location_text
        decimal latitude
        decimal longitude
        string status
        string priority
        int assigned_to_user_id FK
        datetime submitted_at
        datetime accepted_at
        datetime resolution_due_at
        datetime escalated_at
        datetime resolved_at
        datetime rejected_at
        text resolution_note
        text rejection_reason
        datetime created_at
        datetime updated_at
    }

    COMPLAINT_IMAGES {
        int id PK
        int complaint_id FK
        string file_path
        string file_name
        int file_size
        string mime_type
        int width
        int height
        string image_kind
        datetime created_at
    }

    COMPLAINT_STATUS_HISTORY {
        int id PK
        int complaint_id FK
        string from_status
        string to_status
        int actor_user_id FK
        string actor_role
        string note
        datetime created_at
    }

    ESCALATIONS {
        int id PK
        int complaint_id UK, FK
        int escalation_number
        string previous_status
        datetime deadline_at
        datetime escalated_at
        int overdue_seconds
        string trigger_source
        string reason_code
        datetime created_at
    }

    OFFICER_ACTIONS {
        int id PK
        int complaint_id FK
        int officer_user_id FK
        string action_type
        int directed_department_id FK
        text note
        datetime created_at
    }

    NOTIFICATIONS {
        int id PK
        int recipient_user_id FK
        int complaint_id FK
        string trigger_code
        string title
        string body
        bool is_read
        datetime read_at
        datetime created_at
    }

    AUDIT_LOGS {
        int id PK
        int actor_user_id FK
        string action
        string entity_type
        string entity_id
        text metadata_json
        datetime created_at
    }
```

---

## 2. Table Specifications & Constraints

### 2.1 `users`
- **Primary Key:** `id` (INT, AUTO_INCREMENT)
- **Unique Indexes:** `email` (VARCHAR(190), lowercase enforced)
- **Foreign Keys:** `department_id -> departments.id` (ON DELETE RESTRICT, NULL allowed for CITIZEN, SUPERINTENDENT, ADMIN)
- **Check Constraints & Enums:** `role IN ('CITIZEN', 'DEPARTMENT_OFFICER', 'SUPERINTENDENT_OFFICER', 'PLATFORM_ADMIN')`
- **Performance Indexes:** `(role, is_active)`, `(department_id, role)`

### 2.2 `departments`
- **Primary Key:** `id` (INT, AUTO_INCREMENT)
- **Unique Indexes:** `name` (VARCHAR(120)), `code` (VARCHAR(30))
- **Deactivation Guard (BR-15):** Application layer blocks deactivation if active categories or active officers reference the department.

### 2.3 `complaint_categories`
- **Primary Key:** `id` (INT, AUTO_INCREMENT)
- **Unique Indexes:** `name` (VARCHAR(120)), `code` (VARCHAR(40))
- **Foreign Keys:** `department_id -> departments.id` (ON DELETE RESTRICT)
- **Performance Indexes:** `(department_id, is_active)`

### 2.4 `complaints`
- **Primary Key:** `id` (INT, AUTO_INCREMENT)
- **Unique Indexes:** `complaint_number` (VARCHAR(20), format `CT-YYYYMMDD-XXXX`)
- **Foreign Keys:**
  - `citizen_id -> users.id` (ON DELETE RESTRICT)
  - `category_id -> complaint_categories.id` (ON DELETE RESTRICT)
  - `department_id -> departments.id` (ON DELETE RESTRICT)
  - `assigned_to_user_id -> users.id` (ON DELETE SET NULL)
  - `accepted_by_user_id -> users.id` (ON DELETE SET NULL)
  - `resolved_by_user_id -> users.id` (ON DELETE SET NULL)
  - `rejected_by_user_id -> users.id` (ON DELETE SET NULL)
- **Composite Indexes:**
  - `ix_complaints_dept_status_sub (department_id, status, submitted_at)`: Powers Officer queue queries.
  - `ix_complaints_citizen_sub (citizen_id, submitted_at)`: Powers Citizen tracking list.
  - `ix_complaints_status_due (status, resolution_due_at)`: Powers background escalation query.

### 2.5 `complaint_images`
- **Primary Key:** `id` (INT, AUTO_INCREMENT)
- **Foreign Keys:** `complaint_id -> complaints.id` (ON DELETE CASCADE)
- **Storage Rule:** Max 10 images per complaint (enforced in `image_service`).

### 2.6 `complaint_status_history`
- **Primary Key:** `id` (INT, AUTO_INCREMENT)
- **Immutability:** Append-only table. No `UPDATE` or `DELETE` endpoints exposed.
- **Indexes:** `(complaint_id, created_at, id)`, `(to_status, created_at)`.

### 2.7 `escalations`
- **Primary Key:** `id` (INT, AUTO_INCREMENT)
- **Unique Index:** `complaint_id` (enforces exactly-one escalation record per complaint, preventing duplicates under concurrency).
- **Foreign Keys:** `complaint_id -> complaints.id` (ON DELETE RESTRICT).

### 2.8 `officer_actions`
- **Primary Key:** `id` (INT, AUTO_INCREMENT)
- **Foreign Keys:**
  - `complaint_id -> complaints.id` (ON DELETE RESTRICT)
  - `officer_user_id -> users.id` (ON DELETE RESTRICT)
  - `directed_department_id -> departments.id` (ON DELETE RESTRICT)
- **Action Types:** `INSTRUCTION`, `FOLLOW_UP`, `REASSIGN`, `NOTE`.

### 2.9 `audit_logs`
- **Primary Key:** `id` (INT, AUTO_INCREMENT)
- **Immutability:** Append-only table for administrative, configuration, and security events. No mutation routes exist.
- **Privacy:** `metadata_json` excludes raw passwords, bearer tokens, or citizen personal identifiable information.

