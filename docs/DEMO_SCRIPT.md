# CivicTrack — End-to-End Live Demonstration Script (5–10 Minutes)

> **Document:** `docs/DEMO_SCRIPT.md`  
> **Release:** v1.0.0-p0  
> **Target Audience:** Evaluators, Municipal Stakeholders, Reviewers  
> **Duration:** 7 minutes  

---

## 1. Demo Preparation (1 Minute)

Ensure the system is booted with demo configuration:
```bash
# Verify .env has demo mode enabled
ALLOW_DEMO_ESCALATION=true
ESCALATION_WINDOW_MINUTES=5

# Start services and seed initial data
docker compose up -d
docker compose exec api python -m app.seed
```

---

## 2. Walkthrough Steps

### Scene 1: Citizen Complaint Submission (1.5 Minutes)
1. **Navigate to:** `http://localhost:8080/login`
2. **Login as Citizen:**
   - Email: `citizen.jane@civictrack.local`
   - Password: `Citizen@12345`
3. **Action:** Click **"Submit New Complaint"**.
   - Select Department: `Water Supply & Sewage`
   - Category: `Pipe Burst / Water Leakage`
   - Title: `Flooding water burst on 4th Main Street`
   - Description: `Continuous clean water leak damaging street pavement.`
   - Location: `4th Main, Indiranagar`
   - Attach photo evidence (PNG/JPG under 5 MiB).
4. **Result:** Complaint created instantly with unique number `CT-YYYYMMDD-XXXX`. Status is displayed as `SUBMITTED`. Notification received in top nav bar.

---

### Scene 2: Department Officer Acceptance & Progress (1.5 Minutes)
1. **Logout & Login as Officer:**
   - Email: `officer.water@civictrack.local`
   - Password: `Officer@12345`
2. **Action:** Open **Department Queue**.
   - Observe incoming complaint `CT-YYYYMMDD-XXXX` in `SUBMITTED` tab.
   - Click **"Accept Complaint"**.
3. **Result:**
   - Status updates atomically to `IN_PROGRESS`.
   - Resolution deadline (`resolution_due_at`) is automatically calculated from the exact acceptance timestamp.
   - Citizen Jane receives notification `NT-02: Complaint Accepted`.
4. **Action:** Post progress update with comment *"Repair crew dispatched with excavator."*

---

### Scene 3: Deterministic SLA Breach & Escalation (1.5 Minutes)
1. **Explanation:** Under production conditions, unresolved cases escalate after 7 days (10,080 minutes). For this demonstration, our pre-seeded case `CT-DEMO-003` was accepted 8 days ago and is overdue.
2. **Action:** Trigger the background worker run:
   ```bash
   curl -X POST http://localhost:8000/api/v1/internal/escalations/trigger \
     -H "X-Internal-Token: dev-internal-token-change-in-prod"
   ```
3. **Result:**
   - Output indicates `scanned: 6, escalated: 1`.
   - State transition: `IN_PROGRESS -> ESCALATED`.
   - SLA breach notification `NT-05` dispatched to Citizen, Officers, and Superintendent.

---

### Scene 4: Superintendent Oversight & Directives (1.5 Minutes)
1. **Logout & Login as Superintendent:**
   - Email: `superintendent@civictrack.local`
   - Password: `Super@12345`
2. **Action:** Open **Escalation Queue**.
   - Notice complaints sorted by overdue duration descending.
   - Open escalated case `CT-DEMO-003`.
   - Review timeline, deadline breach calculation, and responsible department.
3. **Action:** Issue a Supervisory Directive:
   - Action Type: `INSTRUCTION`
   - Note: *"Expedite replacement pipe valves immediately; submit completion report today."*
4. **Result:** Append-only record created in `officer_actions`. Department officers notified immediately.

---

### Scene 5: Resolution Authority (1 Minute)
1. **Action:** The Superintendent executes final resolution:
   - Click **"Resolve Escalated Complaint"**.
   - Resolution Note: *"City SRE and Water engineers completed valve replacement. Service restored."*
2. **Result:**
   - Complaint status transitions to `RESOLVED`.
   - Status history and resolution timestamp recorded.
   - Case clears from active overdue escalation queue.
   - Final `NT-07` resolution notification delivered to Citizen Jane.

---

## 3. Demo Tear Down

To reset the database back to clean demo state:
```bash
docker compose exec api python -m app.seed
```

