"""Demo seed for Phase 19 (19.4, DEP-009).

Idempotent seed of a runnable demo dataset:

  * 4 departments, 6 categories mapped to departments
  * 1 platform admin, 4 department officers, 1 superintendent, 2 citizens
  * 8 complaints covering every P0 status + 1 overdue candidate
    (ACCEPTED with ``resolution_due_at`` in the past, ready to escalate)

All rows are looked up by natural key (code / email / complaint_number)
before insert, so re-running the command is safe. The overdue candidate
uses ``CT-2026-100009`` so demo scripts can find it deterministically.

Usage:
  python -m app.seed            # idempotent seed (safe to re-run)
  python -m app.seed --check    # verify dataset + overdue candidate exist
  python -m app.seed --reset    # remove demo rows then re-seed (non-prod only)

Password for every demo account comes from ``SEED_PASSWORD``
(default ``Demo@12345``). Demo accounts must never be used in production.
"""

from __future__ import annotations

import argparse
import logging
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.audit import AuditLog
from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import Priority, Role, Status
from app.models.user import User

configure_logging()
logger = logging.getLogger(__name__)

# ── Demo constants (documented in README + RUNBOOK) ──────────────────────────

OVERDUE_COMPLAINT_NUMBER = "CT-2026-100009"
DEMO_SLA_MINUTES = 10_080  # production default; overdue candidate is backdated past it

_DEPARTMENTS: list[tuple[str, str, str]] = [
    ("Water Supply", "WATER", "Drinking water, leakage and drainage"),
    ("Road Maintenance", "ROADS", "Potholes and road repairs"),
    ("Electrical Department", "ELEC", "Streetlights and wiring"),
    ("Sanitation", "SANI", "Garbage and public cleanliness"),
    ("Fire & Rescue", "FIRE", "Fire hazards and rescue operations"),
    ("Parks & Recreation", "PARKS", "Parks, recreation and public green spaces"),
]

_CATEGORIES: list[tuple[str, str, str, Priority]] = [
    ("Water Leakage", "WATER_LEAK", "WATER", Priority.HIGH),
    ("Drainage Blockage", "DRAINAGE", "WATER", Priority.MEDIUM),
    ("Pothole / Damaged Road", "POTHOLE", "ROADS", Priority.HIGH),
    ("Broken Streetlight", "STREETLIGHT", "ELEC", Priority.MEDIUM),
    ("Road Lighting Repair", "ROAD_LIGHTING", "ELEC", Priority.LOW),
    ("Garbage Collection", "GARBAGE", "SANI", Priority.MEDIUM),
    ("Fire Hazard / Smoke", "FIRE_HAZARD", "FIRE", Priority.HIGH),
]

_USERS: list[tuple[str, str, Role, str | None]] = [
    ("Demo Platform Admin", "admin@demo.local", Role.PLATFORM_ADMIN, None),
    ("Water Officer", "officer.water@demo.local", Role.DEPARTMENT_OFFICER, "WATER"),
    ("Roads Officer", "officer.roads@demo.local", Role.DEPARTMENT_OFFICER, "ROADS"),
    ("Electrical Officer", "officer.electrical@demo.local", Role.DEPARTMENT_OFFICER, "ELEC"),
    ("Sanitation Officer", "officer.sanitation@demo.local", Role.DEPARTMENT_OFFICER, "SANI"),
    ("Demo Superintendent", "superintendent@demo.local", Role.SUPERINTENDENT_OFFICER, None),
    ("Demo Citizen One", "citizen1@demo.local", Role.CITIZEN, None),
    ("Demo Citizen Two", "citizen2@demo.local", Role.CITIZEN, None),
]


def _get_department(db: Session, code: str) -> Department | None:
    return db.execute(select(Department).where(Department.code == code)).scalar_one_or_none()


def _get_user(db: Session, email: str) -> User | None:
    return db.execute(
        select(User).where(func.lower(User.email) == email.lower())
    ).scalar_one_or_none()


def _get_category(db: Session, code: str) -> ComplaintCategory | None:
    return db.execute(
        select(ComplaintCategory).where(ComplaintCategory.code == code)
    ).scalar_one_or_none()


def _get_complaint(db: Session, number: str) -> Complaint | None:
    return db.execute(
        select(Complaint).where(Complaint.complaint_number == number)
    ).scalar_one_or_none()


def _ensure_departments(db: Session) -> dict[str, Department]:
    out: dict[str, Department] = {}
    for name, code, description in _DEPARTMENTS:
        dept = _get_department(db, code)
        if dept is None:
            dept = Department(name=name, code=code, description=description, is_active=True)
            db.add(dept)
            db.flush()
            logger.info("event=seed_department_created code=%s", code)
        out[code] = dept
    return out


def _ensure_categories(
    db: Session, departments: dict[str, Department]
) -> dict[str, ComplaintCategory]:
    out: dict[str, ComplaintCategory] = {}
    for name, code, dept_code, priority in _CATEGORIES:
        cat = _get_category(db, code)
        if cat is None:
            cat = ComplaintCategory(
                name=name,
                code=code,
                department_id=departments[dept_code].id,
                default_priority=priority,
                is_active=True,
            )
            db.add(cat)
            db.flush()
            logger.info("event=seed_category_created code=%s department=%s", code, dept_code)
        out[code] = cat
    return out


def _ensure_users(db: Session, departments: dict[str, Department]) -> dict[str, User]:
    password_hash = hash_password(settings.seed_password)
    out: dict[str, User] = {}
    for full_name, email, role, dept_code in _USERS:
        user = _get_user(db, email)
        if user is None:
            user = User(
                full_name=full_name,
                email=email.lower(),
                password_hash=password_hash,
                role=role,
                department_id=departments[dept_code].id if dept_code else None,
                is_active=True,
            )
            db.add(user)
            db.flush()
            logger.info("event=seed_user_created email=%s role=%s", email, role.value)
        out[email] = user
    return out


def _ensure_complaints(
    db: Session,
    categories: dict[str, ComplaintCategory],
    users: dict[str, User],
) -> list[Complaint]:
    """Create one complaint per P0 status plus the overdue candidate."""
    now = utcnow()
    sla_seconds = DEMO_SLA_MINUTES * 60
    citizen1 = users["citizen1@demo.local"]
    citizen2 = users["citizen2@demo.local"]
    roads_officer = users["officer.roads@demo.local"]
    electrical_officer = users["officer.electrical@demo.local"]
    water_officer = users["officer.water@demo.local"]

    def spec(
        number: str,
        citizen: User,
        category_code: str,
        title: str,
        description: str,
        status: Status,
        priority: Priority,
        submitted_days_ago: int,
        accepted_days_ago: int | None = None,
        rejected_days_ago: int | None = None,
        escalated_days_ago: int | None = None,
        resolved_days_ago: int | None = None,
        reopened_days_ago: int | None = None,
        assigned: User | None = None,
        due_offset_minutes: int | None = None,
        location: str | None = None,
    ) -> dict:
        category = categories[category_code]
        submitted = now - timedelta(days=submitted_days_ago)
        accepted = (
            now - timedelta(days=accepted_days_ago) if accepted_days_ago is not None else None
        )
        due: object = None
        if accepted is not None:
            if due_offset_minutes is not None:
                due = accepted + timedelta(minutes=due_offset_minutes)
            else:
                due = accepted + timedelta(minutes=DEMO_SLA_MINUTES)
        return {
            "complaint_number": number,
            "citizen_id": citizen.id,
            "category_id": category.id,
            "department_id": category.department_id,
            "title": title,
            "description": description,
            "location_text": location,
            "status": status,
            "priority": priority,
            "assigned_to_user_id": assigned.id if assigned else None,
            "assigned_at": accepted,
            "submitted_at": submitted,
            "accepted_at": accepted,
            "accepted_by_user_id": assigned.id if accepted and assigned else None,
            "sla_seconds": sla_seconds if accepted is not None else None,
            "resolution_due_at": due,
            "escalated_at": now - timedelta(days=escalated_days_ago)
            if escalated_days_ago is not None
            else None,
            "resolved_at": now - timedelta(days=resolved_days_ago)
            if resolved_days_ago is not None
            else None,
            "resolved_by_user_id": assigned.id
            if resolved_days_ago is not None and assigned
            else None,
            "resolution_note": "Demo resolution: field visit completed."
            if resolved_days_ago is not None
            else None,
            "rejected_at": now - timedelta(days=rejected_days_ago)
            if rejected_days_ago is not None
            else None,
            "rejected_by_user_id": roads_officer.id if rejected_days_ago is not None else None,
            "rejection_reason": (
                "Demo rejection: issue falls outside department scope."
                if rejected_days_ago is not None
                else None
            ),
            "reopened_at": now - timedelta(days=reopened_days_ago)
            if reopened_days_ago is not None
            else None,
        }

    specs = [
        spec(
            "CT-2026-100001",
            citizen1,
            "POTHOLE",
            "Crack on footpath near market",
            "Footpath is cracked and uneven near the market entrance.",
            Status.SUBMITTED,
            Priority.MEDIUM,
            submitted_days_ago=1,
        ),
        spec(
            "CT-2026-100002",
            citizen2,
            "STREETLIGHT",
            "Streetlight flickering on 4th Cross",
            "Streetlight flickers every few seconds at night.",
            Status.PENDING_DEPARTMENT_REVIEW,
            Priority.MEDIUM,
            submitted_days_ago=2,
        ),
        spec(
            "CT-2026-100003",
            citizen1,
            "WATER_LEAK",
            "Water leakage near borewell",
            "Pipe leaking steadily near the borewell; water pooling.",
            Status.ACCEPTED,
            Priority.HIGH,
            submitted_days_ago=3,
            accepted_days_ago=2,
            assigned=water_officer,
        ),
        spec(
            "CT-2026-100004",
            citizen2,
            "DRAINAGE",
            "Blocked drain on Lake Road",
            "Drain blocked; wastewater overflowing onto the road.",
            Status.IN_PROGRESS,
            Priority.HIGH,
            submitted_days_ago=4,
            accepted_days_ago=3,
            assigned=water_officer,
        ),
        spec(
            "CT-2026-100005",
            citizen1,
            "GARBAGE",
            "Duplicate complaint (out of scope)",
            "Request logged against the wrong department.",
            Status.REJECTED,
            Priority.LOW,
            submitted_days_ago=5,
            rejected_days_ago=4,
        ),
        spec(
            "CT-2026-100006",
            citizen2,
            "POTHOLE",
            "Large pothole at bus stand",
            "Large pothole at the bus stand causing vehicle damage.",
            Status.ESCALATED,
            Priority.HIGH,
            submitted_days_ago=10,
            accepted_days_ago=9,
            escalated_days_ago=2,
            assigned=roads_officer,
        ),
        spec(
            "CT-2026-100007",
            citizen1,
            "STREETLIGHT",
            "Streetlight pole damaged",
            "Pole leaning dangerously after a storm.",
            Status.RESOLVED,
            Priority.MEDIUM,
            submitted_days_ago=12,
            accepted_days_ago=11,
            resolved_days_ago=2,
            assigned=electrical_officer,
        ),
        spec(
            "CT-2026-100008",
            citizen2,
            "ROAD_LIGHTING",
            "Dim lights on side lane",
            "Reopened: lighting still dim after initial repair.",
            Status.REOPENED,
            Priority.MEDIUM,
            submitted_days_ago=15,
            accepted_days_ago=14,
            resolved_days_ago=5,
            reopened_days_ago=1,
            assigned=electrical_officer,
        ),
        # Guaranteed overdue candidate: ACCEPTED, deadline already past.
        spec(
            OVERDUE_COMPLAINT_NUMBER,
            citizen1,
            "POTHOLE",
            "Overdue demo pothole (escalation ready)",
            "Demo complaint accepted long ago with a past deadline. "
            "The escalation worker should escalate this automatically.",
            Status.ACCEPTED,
            Priority.HIGH,
            submitted_days_ago=9,
            accepted_days_ago=8,
            assigned=roads_officer,
            location="Demo Street, near bus stand",
        ),
    ]

    created: list[Complaint] = []
    for data in specs:
        existing = _get_complaint(db, data["complaint_number"])
        if existing is not None:
            created.append(existing)
            continue
        complaint = Complaint(**data)
        db.add(complaint)
        db.flush()
        logger.info(
            "event=seed_complaint_created number=%s status=%s",
            complaint.complaint_number,
            complaint.status.value,
        )
        created.append(complaint)

    # The overdue candidate must have escalated_at IS NULL and a past due date.
    overdue = next(c for c in created if c.complaint_number == OVERDUE_COMPLAINT_NUMBER)
    if overdue.escalated_at is not None or overdue.resolution_due_at is None:
        logger.warning("event=seed_overdue_unexpected_state number=%s", overdue.complaint_number)
    return created


def ensure_overdue_candidate(db: Session) -> Complaint | None:
    """Return the overdue candidate or None if the seed has not run."""
    return _get_complaint(db, OVERDUE_COMPLAINT_NUMBER)


def verify_dataset(db: Session) -> dict:
    """Check that every status + the overdue candidate exist; raise if not."""
    statuses = set()
    for status in Status:
        count = db.execute(
            select(func.count()).select_from(Complaint).where(Complaint.status == status)
        ).scalar_one()
        statuses.add((status.value, int(count)))
    overdue = ensure_overdue_candidate(db)
    overdue_ok = bool(
        overdue
        and overdue.status == Status.ACCEPTED
        and overdue.resolution_due_at is not None
        and overdue.resolution_due_at <= utcnow()
        and overdue.escalated_at is None
    )
    if overdue is None or not overdue_ok:
        raise RuntimeError(
            f"Overdue candidate {OVERDUE_COMPLAINT_NUMBER} missing or not overdue (found: {overdue})"
        )
    for status_value, count in statuses:
        if count == 0:
            raise RuntimeError(f"Seed missing a complaint in status {status_value}")
    return {
        "overdue_complaint_number": OVERDUE_COMPLAINT_NUMBER,
        "status_counts": dict(statuses),
        "checks": ["all_statuses_present", "overdue_candidate_ready"],
    }


def reset_demo_data(db: Session) -> None:
    """Remove demo rows (non-production only) so `--reset` can re-seed cleanly."""
    if settings.is_production:
        raise RuntimeError("Refusing to reset demo data in production")
    db.query(Complaint).delete()
    db.query(AuditLog).delete()
    for row in _USERS:
        user = _get_user(db, row[1])
        if user is not None:
            db.delete(user)
    db.flush()
    db.query(ComplaintCategory).delete()
    db.query(Department).delete()
    db.flush()
    logger.info("event=seed_reset_demo_rows_removed")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="CivicTrack demo seed (Phase 19)")
    parser.add_argument("--check", action="store_true", help="Verify seed instead of writing it")
    parser.add_argument(
        "--reset", action="store_true", help="Delete demo rows and re-seed (non-prod only)"
    )
    args = parser.parse_args(argv)

    # Auto-create tables so local/sqlite runs work even before the first
    # Alembic migration has been applied.
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if args.check:
            summary = verify_dataset(db)
            logger.info("event=seed_check_passed summary=%s", summary)
            print(f"seed check passed: {summary}")
            return

        if args.reset:
            reset_demo_data(db)
            db.commit()

        departments = _ensure_departments(db)
        categories = _ensure_categories(db, departments)
        users = _ensure_users(db, departments)
        _ensure_complaints(db, categories, users)
        db.commit()

        summary = verify_dataset(db)
        logger.info(
            "event=seed_complete departments=%s categories=%s overdue=%s",
            len(departments),
            len(categories),
            summary["overdue_complaint_number"],
        )
        print(f"seed complete: {summary}")
        print("Demo accounts (password: SEED_PASSWORD, default Demo@12345):")
        for _name, email, role, _dept in _USERS:
            print(f"  {email}  {role.value}")


if __name__ == "__main__":
    main()
