"""
CivicTrack — Production & Demo Seed Data Script (DEP-009, US-ADM-06, BR-01..BR-18)
Idempotent creation of standard departments, categories, demo users,
and complaints across all P0 statuses, including one guaranteed overdue candidate.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.logging import configure_logging
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import OfficerActionType, Priority, Role, Status, TriggerSource
from app.models.escalation import Escalation
from app.models.history import ComplaintStatusHistory
from app.models.notification import Notification
from app.models.officer_action import OfficerAction
from app.models.user import User

configure_logging()
logger = logging.getLogger(__name__)


def _user_id(value: Any) -> int | None:
    """Return the id of an optional ORM user value."""
    return value.id if value is not None else None


def seed_database(session: Session | None = None) -> None:
    db = session or SessionLocal()
    should_close = session is None
    try:
        now = utcnow()
        logger.info("event=seed_start timestamp=%s", now.isoformat())

        # -------------------------------------------------------------
        # 1. Departments (Idempotent)
        # -------------------------------------------------------------
        departments_data: list[dict[str, Any]] = [
            {
                "name": "Water Supply & Sewage",
                "code": "WTR",
                "description": "Municipal water distribution and sewerage",
            },
            {
                "name": "Roads & Transport",
                "code": "RDS",
                "description": "Road maintenance, traffic signals, and pathways",
            },
            {
                "name": "Electricity & Lighting",
                "code": "ELE",
                "description": "Street lighting and public electrical utilities",
            },
            {
                "name": "Waste Management & Sanitation",
                "code": "SAN",
                "description": "Solid waste collection and urban sanitation",
            },
        ]
        dept_map: dict[str, Department] = {}
        for d_info in departments_data:
            dept = db.execute(
                select(Department).where(Department.code == d_info["code"])
            ).scalar_one_or_none()
            if not dept:
                dept = Department(
                    name=d_info["name"],
                    code=d_info["code"],
                    description=d_info["description"],
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                db.add(dept)
                db.flush()
                logger.info("event=seed_department_created code=%s", d_info["code"])
            dept_map[d_info["code"]] = dept

        # -------------------------------------------------------------
        # 2. Categories (Idempotent)
        # -------------------------------------------------------------
        categories_data: list[dict[str, Any]] = [
            {
                "name": "Pipe Burst / Water Leakage",
                "code": "WTR_BURST",
                "dept": "WTR",
                "priority": Priority.HIGH,
            },
            {
                "name": "Pothole / Road Damage",
                "code": "RDS_POTHOLE",
                "dept": "RDS",
                "priority": Priority.MEDIUM,
            },
            {
                "name": "Streetlight Outage",
                "code": "ELE_LIGHT",
                "dept": "ELE",
                "priority": Priority.LOW,
            },
            {
                "name": "Garbage Dump Overflow",
                "code": "SAN_GARBAGE",
                "dept": "SAN",
                "priority": Priority.MEDIUM,
            },
        ]
        cat_map: dict[str, ComplaintCategory] = {}
        for c_info in categories_data:
            cat = db.execute(
                select(ComplaintCategory).where(ComplaintCategory.code == c_info["code"])
            ).scalar_one_or_none()
            if not cat:
                cat = ComplaintCategory(
                    name=c_info["name"],
                    code=c_info["code"],
                    department_id=dept_map[c_info["dept"]].id,
                    default_priority=c_info["priority"],
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                db.add(cat)
                db.flush()
                logger.info("event=seed_category_created code=%s", c_info["code"])
            cat_map[c_info["code"]] = cat

        # -------------------------------------------------------------
        # 3. Users (Idempotent)
        # -------------------------------------------------------------
        users_data: list[dict[str, Any]] = [
            {
                "email": "admin@civictrack.local",
                "full_name": "Platform Administrator",
                "role": Role.PLATFORM_ADMIN,
                "dept": None,
                "password": "Admin@12345",
            },
            {
                "email": "superintendent@civictrack.local",
                "full_name": "City Superintendent",
                "role": Role.SUPERINTENDENT_OFFICER,
                "dept": None,
                "password": "Super@12345",
            },
            {
                "email": "officer.water@civictrack.local",
                "full_name": "Water Department Officer",
                "role": Role.DEPARTMENT_OFFICER,
                "dept": "WTR",
                "password": "Officer@12345",
            },
            {
                "email": "officer.roads@civictrack.local",
                "full_name": "Roads Department Officer",
                "role": Role.DEPARTMENT_OFFICER,
                "dept": "RDS",
                "password": "Officer@12345",
            },
            {
                "email": "citizen.jane@civictrack.local",
                "full_name": "Jane Citizen",
                "role": Role.CITIZEN,
                "dept": None,
                "password": "Citizen@12345",
            },
            {
                "email": "citizen.john@civictrack.local",
                "full_name": "John Citizen",
                "role": Role.CITIZEN,
                "dept": None,
                "password": "Citizen@12345",
            },
        ]
        user_map: dict[str, User] = {}
        for u_info in users_data:
            user = db.execute(
                select(User).where(User.email == u_info["email"])
            ).scalar_one_or_none()
            if not user:
                user = User(
                    email=u_info["email"],
                    full_name=u_info["full_name"],
                    password_hash=hash_password(u_info["password"]),
                    role=u_info["role"],
                    department_id=dept_map[u_info["dept"]].id if u_info["dept"] else None,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                db.add(user)
                db.flush()
                logger.info("event=seed_user_created role=%s", u_info["role"].value)
            user_map[u_info["email"]] = user

        # -------------------------------------------------------------
        # 4. Complaints in Every P0 Status (Idempotent)
        # -------------------------------------------------------------
        citizen_jane = user_map["citizen.jane@civictrack.local"]
        citizen_john = user_map["citizen.john@civictrack.local"]
        officer_water = user_map["officer.water@civictrack.local"]
        officer_roads = user_map["officer.roads@civictrack.local"]
        superintendent = user_map["superintendent@civictrack.local"]

        # Default SLA window: 7 days (604,800 seconds)
        sla_seconds = 7 * 24 * 3600

        complaints_data: list[dict[str, Any]] = [
            # 1. SUBMITTED
            {
                "number": "CT-DEMO-001",
                "title": "Overflowing waste container at Central Park",
                "desc": "Garbage has not been collected for three days and is overflowing into pedestrian walkway.",
                "status": Status.SUBMITTED,
                "priority": Priority.MEDIUM,
                "cat": "SAN_GARBAGE",
                "dept": "SAN",
                "citizen": citizen_jane,
                "sub_time": now - timedelta(hours=3),
                "loc": "Central Park North Entrance",
                "lat": Decimal("12.971600"),
                "lon": Decimal("77.594600"),
            },
            # 2. IN_PROGRESS (Normal SLA, healthy)
            {
                "number": "CT-DEMO-002",
                "title": "Low water pressure on 5th Cross Road",
                "desc": "Residents report low water pressure throughout the morning supply window.",
                "status": Status.IN_PROGRESS,
                "priority": Priority.MEDIUM,
                "cat": "WTR_BURST",
                "dept": "WTR",
                "citizen": citizen_jane,
                "sub_time": now - timedelta(days=2),
                "accepted_time": now - timedelta(days=2, hours=-1),
                "accepted_by": officer_water,
                "loc": "5th Cross Road, Indiranagar",
                "lat": Decimal("12.978400"),
                "lon": Decimal("77.640800"),
            },
            # 3. IN_PROGRESS (GUARANTEED OVERDUE CANDIDATE - Accepted 8 days ago!)
            {
                "number": "CT-DEMO-003",
                "title": "Major underground pipeline rupture on Market Road",
                "desc": "Continuous water outflow flooding commercial area; immediate intervention required.",
                "status": Status.IN_PROGRESS,
                "priority": Priority.HIGH,
                "cat": "WTR_BURST",
                "dept": "WTR",
                "citizen": citizen_jane,
                "sub_time": now - timedelta(days=8, hours=2),
                "accepted_time": now - timedelta(days=8),
                "accepted_by": officer_water,
                "loc": "Market Road Commercial Complex",
                "lat": Decimal("12.965000"),
                "lon": Decimal("77.585000"),
            },
            # 4. ESCALATED (Accepted 9 days ago, escalated 2 days ago)
            {
                "number": "CT-DEMO-004",
                "title": "Dangerous deep pothole near Metro Station",
                "desc": "Deep pothole causing vehicular damage and traffic bottleneck near metro pillar 142.",
                "status": Status.ESCALATED,
                "priority": Priority.HIGH,
                "cat": "RDS_POTHOLE",
                "dept": "RDS",
                "citizen": citizen_john,
                "sub_time": now - timedelta(days=10),
                "accepted_time": now - timedelta(days=9),
                "accepted_by": officer_roads,
                "escalated_time": now - timedelta(days=2),
                "loc": "Metro Pillar 142, Outer Ring Road",
                "lat": Decimal("12.920000"),
                "lon": Decimal("77.680000"),
            },
            # 5. RESOLVED
            {
                "number": "CT-DEMO-005",
                "title": "Streetlight flickering continuously on 2nd Avenue",
                "desc": "Street fixture ballast faulty causing rapid strobe effect at night.",
                "status": Status.RESOLVED,
                "priority": Priority.LOW,
                "cat": "ELE_LIGHT",
                "dept": "ELE",
                "citizen": citizen_jane,
                "sub_time": now - timedelta(days=5),
                "accepted_time": now - timedelta(days=4),
                "resolved_time": now - timedelta(days=1),
                "resolved_by": superintendent,
                "res_note": "Replaced faulty sodium bulb and igniter with LED fixture. Tested and confirmed operational.",
                "loc": "2nd Avenue, Koramangala",
                "lat": Decimal("12.935000"),
                "lon": Decimal("77.625000"),
            },
            # 6. REJECTED
            {
                "number": "CT-DEMO-006",
                "title": "Private garden water fountain maintenance",
                "desc": "Requesting city crew to clean decorative fountain inside gated apartment complex.",
                "status": Status.REJECTED,
                "priority": Priority.LOW,
                "cat": "WTR_BURST",
                "dept": "WTR",
                "citizen": citizen_john,
                "sub_time": now - timedelta(days=3),
                "rejected_time": now - timedelta(days=2),
                "rejected_by": officer_water,
                "rej_reason": "Private residential property asset outside municipal civic maintenance jurisdiction.",
                "loc": "Palm Grove Residences, Villa 12",
                "lat": Decimal("12.950000"),
                "lon": Decimal("77.610000"),
            },
        ]

        for cmp_data in complaints_data:
            existing = db.execute(
                select(Complaint).where(Complaint.complaint_number == cmp_data["number"])
            ).scalar_one_or_none()
            if existing:
                continue

            sub_at = cmp_data["sub_time"]
            accepted_at = cmp_data.get("accepted_time")
            due_at = accepted_at + timedelta(seconds=sla_seconds) if accepted_at else None

            c = Complaint(
                complaint_number=cmp_data["number"],
                citizen_id=cmp_data["citizen"].id,
                category_id=cat_map[cmp_data["cat"]].id,
                department_id=dept_map[cmp_data["dept"]].id,
                title=cmp_data["title"],
                description=cmp_data["desc"],
                location_text=cmp_data["loc"],
                latitude=cmp_data["lat"],
                longitude=cmp_data["lon"],
                status=cmp_data["status"],
                priority=cmp_data["priority"],
                submitted_at=sub_at,
                accepted_at=accepted_at,
                accepted_by_user_id=_user_id(cmp_data.get("accepted_by")),
                sla_seconds=sla_seconds if accepted_at else None,
                resolution_due_at=due_at,
                escalated_at=cmp_data.get("escalated_time"),
                resolved_at=cmp_data.get("resolved_time"),
                resolved_by_user_id=_user_id(cmp_data.get("resolved_by")),
                resolution_note=cmp_data.get("res_note"),
                rejected_at=cmp_data.get("rejected_time"),
                rejected_by_user_id=_user_id(cmp_data.get("rejected_by")),
                rejection_reason=cmp_data.get("rej_reason"),
                created_at=sub_at,
                updated_at=now,
            )
            db.add(c)
            db.flush()

            # Add History row for submission
            h_sub = ComplaintStatusHistory(
                complaint_id=c.id,
                from_status=None,
                to_status=Status.SUBMITTED,
                actor_user_id=cmp_data["citizen"].id,
                actor_role=Role.CITIZEN.value,
                note="Complaint submitted by citizen",
                created_at=sub_at,
            )
            db.add(h_sub)

            # History and Notification for ACCEPTED / IN_PROGRESS
            if accepted_at:
                h_acc = ComplaintStatusHistory(
                    complaint_id=c.id,
                    from_status=Status.SUBMITTED,
                    to_status=Status.IN_PROGRESS,
                    actor_user_id=_user_id(cmp_data.get("accepted_by")),
                    actor_role=Role.DEPARTMENT_OFFICER.value,
                    note="Complaint accepted for investigation",
                    created_at=accepted_at,
                )
                db.add(h_acc)

            # Escalation entry if ESCALATED
            if cmp_data.get("escalated_time"):
                esc_time = cmp_data["escalated_time"]
                h_esc = ComplaintStatusHistory(
                    complaint_id=c.id,
                    from_status=Status.IN_PROGRESS,
                    to_status=Status.ESCALATED,
                    actor_user_id=None,
                    actor_role="SYSTEM",
                    note="Automated SLA breach escalation",
                    created_at=esc_time,
                )
                db.add(h_esc)

                esc_rec = Escalation(
                    complaint_id=c.id,
                    escalation_number=1,
                    previous_status=Status.IN_PROGRESS,
                    deadline_at=due_at,
                    escalated_at=esc_time,
                    overdue_seconds=int((esc_time - due_at).total_seconds()),
                    trigger_source=TriggerSource.DEMO_SEED,
                    reason_code="SLA_BREACH",
                    created_at=esc_time,
                )
                db.add(esc_rec)

                # Add a superintendent instruction
                action = OfficerAction(
                    complaint_id=c.id,
                    officer_user_id=superintendent.id,
                    action_type=OfficerActionType.INSTRUCTION,
                    directed_department_id=dept_map["RDS"].id,
                    note="High traffic corridor - expedite asphalt repair crew before morning peak hours.",
                    created_at=esc_time + timedelta(hours=2),
                )
                db.add(action)

            # Resolution entry if RESOLVED
            if cmp_data.get("resolved_time"):
                res_time = cmp_data["resolved_time"]
                h_res = ComplaintStatusHistory(
                    complaint_id=c.id,
                    from_status=Status.IN_PROGRESS,
                    to_status=Status.RESOLVED,
                    actor_user_id=_user_id(cmp_data.get("resolved_by")),
                    actor_role=Role.SUPERINTENDENT_OFFICER.value,
                    note=cmp_data.get("res_note"),
                    created_at=res_time,
                )
                db.add(h_res)

            # Rejection entry if REJECTED
            if cmp_data.get("rejected_time"):
                rej_time = cmp_data["rejected_time"]
                h_rej = ComplaintStatusHistory(
                    complaint_id=c.id,
                    from_status=Status.SUBMITTED,
                    to_status=Status.REJECTED,
                    actor_user_id=_user_id(cmp_data.get("rejected_by")),
                    actor_role=Role.DEPARTMENT_OFFICER.value,
                    note=cmp_data.get("rej_reason"),
                    created_at=rej_time,
                )
                db.add(h_rej)

            # Seed notification for citizen
            notif = Notification(
                recipient_user_id=cmp_data["citizen"].id,
                complaint_id=c.id,
                trigger_code="NT-01",
                title=f"Complaint {c.complaint_number} Update",
                body=f"Your complaint '{c.title}' is currently {c.status.value}.",
                is_read=False,
                created_at=sub_at,
            )
            db.add(notif)
            logger.info(
                "event=seed_complaint_created number=%s status=%s",
                c.complaint_number,
                c.status.value,
            )

        db.commit()
        logger.info("event=seed_completed status=success")
    except Exception as exc:
        db.rollback()
        logger.error("event=seed_failed error=%s", str(exc), exc_info=True)
        raise
    finally:
        if should_close:
            db.close()


def main() -> None:
    seed_database()


if __name__ == "__main__":
    main()
