"""
CivicTrack — Administration Service (FR-046, FR-047, FR-048, BR-15, US-ADM-02..04)
"""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.errors import Conflict, NotFound, UnprocessableEntity
from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import Role, Status
from app.models.history import ComplaintStatusHistory
from app.models.user import User
from app.schemas.admin import (
    CategoryCreate,
    CategoryDetailOut,
    CategoryUpdate,
    DepartmentActivityItem,
    DepartmentCreate,
    DepartmentUpdate,
    PlatformActivityResponse,
    RecentEventItem,
)
from app.schemas.department import DepartmentOut
from app.services.audit_service import record_audit_event

logger = logging.getLogger(__name__)


# ── Department Management (FR-046, BR-15, US-ADM-02) ─────────────────────────


def list_departments(
    db: Session,
    is_active: bool | None = None,
) -> list[Department]:
    """List all departments, optionally filtered by active status."""
    stmt = select(Department)
    if is_active is not None:
        stmt = stmt.where(Department.is_active == is_active)
    return list(db.scalars(stmt.order_by(Department.name.asc())).all())


def create_department(
    db: Session,
    data: DepartmentCreate,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Department:
    """Create a new department (FR-046)."""
    name_clean = data.name.strip()
    code_clean = data.code.strip().upper()

    existing_name = db.scalar(
        select(Department).where(func.lower(Department.name) == name_clean.lower())
    )
    if existing_name:
        raise Conflict(
            message=f"Department with name '{name_clean}' already exists.",
            error_code="DEPARTMENT_NAME_EXISTS",
        )

    existing_code = db.scalar(select(Department).where(func.upper(Department.code) == code_clean))
    if existing_code:
        raise Conflict(
            message=f"Department with code '{code_clean}' already exists.",
            error_code="DEPARTMENT_CODE_EXISTS",
        )

    dept = Department(
        name=name_clean,
        code=code_clean,
        description=data.description.strip() if data.description else None,
        is_active=data.is_active,
    )
    db.add(dept)
    db.flush()

    record_audit_event(
        db=db,
        actor_user_id=actor.id,
        actor_role=actor.role.value,
        action="DEPARTMENT_CREATED",
        entity_type="DEPARTMENT",
        entity_id=str(dept.id),
        metadata={"name": dept.name, "code": dept.code, "is_active": dept.is_active},
        ip_address=ip_address,
        user_agent=user_agent,
        commit=False,
    )

    db.commit()
    db.refresh(dept)
    return dept


def update_department(
    db: Session,
    dept_id: int,
    data: DepartmentUpdate,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Department:
    """
    Update department metadata or active status (FR-046, BR-15).
    Blocks deactivation if active categories or active officers reference it.
    """
    dept = db.get(Department, dept_id)
    if not dept:
        raise NotFound(message="Department not found.", error_code="NOT_FOUND")

    changes: dict[str, str | bool] = {}

    if data.name is not None:
        name_clean = data.name.strip()
        if name_clean.lower() != dept.name.lower():
            conflict = db.scalar(
                select(Department).where(
                    func.lower(Department.name) == name_clean.lower(),
                    Department.id != dept.id,
                )
            )
            if conflict:
                raise Conflict(
                    message=f"Department with name '{name_clean}' already exists.",
                    error_code="DEPARTMENT_NAME_EXISTS",
                )
            dept.name = name_clean
            changes["name"] = name_clean

    if data.code is not None:
        code_clean = data.code.strip().upper()
        if code_clean != dept.code.upper():
            conflict = db.scalar(
                select(Department).where(
                    func.upper(Department.code) == code_clean,
                    Department.id != dept.id,
                )
            )
            if conflict:
                raise Conflict(
                    message=f"Department with code '{code_clean}' already exists.",
                    error_code="DEPARTMENT_CODE_EXISTS",
                )
            dept.code = code_clean
            changes["code"] = code_clean

    if data.description is not None:
        dept.description = data.description.strip() or None
        changes["description"] = dept.description or ""

    if data.is_active is not None and data.is_active != dept.is_active:
        if not data.is_active and dept.is_active:
            # Deactivation Guard (BR-15): check active categories and active officers
            active_cats = (
                db.scalar(
                    select(func.count(ComplaintCategory.id)).where(
                        ComplaintCategory.department_id == dept.id,
                        ComplaintCategory.is_active.is_(True),
                    )
                )
                or 0
            )

            active_officers = (
                db.scalar(
                    select(func.count(User.id)).where(
                        User.department_id == dept.id,
                        User.role == Role.DEPARTMENT_OFFICER,
                        User.is_active.is_(True),
                    )
                )
                or 0
            )

            if active_cats > 0 or active_officers > 0:
                raise Conflict(
                    message=(
                        f"Cannot deactivate department with {active_cats} active categories "
                        f"and {active_officers} active officers."
                    ),
                    error_code="DEPARTMENT_IN_USE",
                    details={
                        "active_categories": active_cats,
                        "active_officers": active_officers,
                    },
                )

        dept.is_active = data.is_active
        changes["is_active"] = data.is_active

    record_audit_event(
        db=db,
        actor_user_id=actor.id,
        actor_role=actor.role.value,
        action="DEPARTMENT_UPDATED",
        entity_type="DEPARTMENT",
        entity_id=str(dept.id),
        metadata=changes,
        ip_address=ip_address,
        user_agent=user_agent,
        commit=False,
    )

    db.commit()
    db.refresh(dept)
    return dept


# ── Category Management (FR-047, US-ADM-03) ───────────────────────────────────


def list_categories(
    db: Session,
    department_id: int | None = None,
    is_active: bool | None = None,
) -> list[CategoryDetailOut]:
    """List complaint categories with joined department."""
    stmt = select(ComplaintCategory).options(joinedload(ComplaintCategory.department))

    if department_id is not None:
        stmt = stmt.where(ComplaintCategory.department_id == department_id)
    if is_active is not None:
        stmt = stmt.where(ComplaintCategory.is_active == is_active)

    categories = db.scalars(stmt.order_by(ComplaintCategory.name.asc())).all()
    return [
        CategoryDetailOut(
            id=c.id,
            name=c.name,
            code=c.code,
            description=c.description,
            department_id=c.department_id,
            department=DepartmentOut.model_validate(c.department),
            default_priority=c.default_priority,
            is_active=c.is_active,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in categories
    ]


def create_category(
    db: Session,
    data: CategoryCreate,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> CategoryDetailOut:
    """Create a new complaint category mapped to an active department (FR-047)."""
    name_clean = data.name.strip()
    code_clean = data.code.strip().upper()

    existing_name = db.scalar(
        select(ComplaintCategory).where(func.lower(ComplaintCategory.name) == name_clean.lower())
    )
    if existing_name:
        raise Conflict(
            message=f"Category with name '{name_clean}' already exists.",
            error_code="CATEGORY_NAME_EXISTS",
        )

    existing_code = db.scalar(
        select(ComplaintCategory).where(func.upper(ComplaintCategory.code) == code_clean)
    )
    if existing_code:
        raise Conflict(
            message=f"Category with code '{code_clean}' already exists.",
            error_code="CATEGORY_CODE_EXISTS",
        )

    target_dept = db.get(Department, data.department_id)
    if not target_dept or not target_dept.is_active:
        raise UnprocessableEntity(
            message="Department does not exist or is inactive.",
            error_code="INVALID_DEPARTMENT",
        )

    category = ComplaintCategory(
        name=name_clean,
        code=code_clean,
        description=data.description.strip() if data.description else None,
        department_id=target_dept.id,
        default_priority=data.default_priority,
        is_active=data.is_active,
    )
    db.add(category)
    db.flush()

    record_audit_event(
        db=db,
        actor_user_id=actor.id,
        actor_role=actor.role.value,
        action="CATEGORY_CREATED",
        entity_type="CATEGORY",
        entity_id=str(category.id),
        metadata={
            "name": category.name,
            "code": category.code,
            "department_id": category.department_id,
            "is_active": category.is_active,
        },
        ip_address=ip_address,
        user_agent=user_agent,
        commit=False,
    )

    db.commit()
    db.refresh(category)

    return CategoryDetailOut(
        id=category.id,
        name=category.name,
        code=category.code,
        description=category.description,
        department_id=category.department_id,
        department=DepartmentOut.model_validate(target_dept),
        default_priority=category.default_priority,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def update_category(
    db: Session,
    category_id: int,
    data: CategoryUpdate,
    actor: User,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> CategoryDetailOut:
    """
    Update category metadata, default priority, active state, or mapped department (FR-047).
    Department remapping requires target department to be active.
    Remapping affects future complaints only.
    """
    category = db.execute(
        select(ComplaintCategory)
        .options(joinedload(ComplaintCategory.department))
        .where(ComplaintCategory.id == category_id)
    ).scalar_one_or_none()

    if not category:
        raise NotFound(message="Category not found.", error_code="NOT_FOUND")

    changes: dict[str, str | int | bool] = {}
    note: str | None = None

    if data.name is not None:
        name_clean = data.name.strip()
        if name_clean.lower() != category.name.lower():
            conflict = db.scalar(
                select(ComplaintCategory).where(
                    func.lower(ComplaintCategory.name) == name_clean.lower(),
                    ComplaintCategory.id != category.id,
                )
            )
            if conflict:
                raise Conflict(
                    message=f"Category with name '{name_clean}' already exists.",
                    error_code="CATEGORY_NAME_EXISTS",
                )
            category.name = name_clean
            changes["name"] = name_clean

    if data.code is not None:
        code_clean = data.code.strip().upper()
        if code_clean != category.code.upper():
            conflict = db.scalar(
                select(ComplaintCategory).where(
                    func.upper(ComplaintCategory.code) == code_clean,
                    ComplaintCategory.id != category.id,
                )
            )
            if conflict:
                raise Conflict(
                    message=f"Category with code '{code_clean}' already exists.",
                    error_code="CATEGORY_CODE_EXISTS",
                )
            category.code = code_clean
            changes["code"] = code_clean

    if data.description is not None:
        category.description = data.description.strip() or None
        changes["description"] = category.description or ""

    if data.default_priority is not None:
        category.default_priority = data.default_priority
        changes["default_priority"] = data.default_priority.value

    if data.is_active is not None:
        category.is_active = data.is_active
        changes["is_active"] = data.is_active

    if data.department_id is not None and data.department_id != category.department_id:
        new_dept = db.get(Department, data.department_id)
        if not new_dept or not new_dept.is_active:
            raise UnprocessableEntity(
                message="Target department does not exist or is inactive.",
                error_code="INVALID_DEPARTMENT",
            )
        old_dept_id = category.department_id
        category.department_id = new_dept.id
        category.department = new_dept
        changes["old_department_id"] = old_dept_id
        changes["new_department_id"] = new_dept.id
        note = "Affects new complaints only."

        record_audit_event(
            db=db,
            actor_user_id=actor.id,
            actor_role=actor.role.value,
            action="CATEGORY_REMAPPED",
            entity_type="CATEGORY",
            entity_id=str(category.id),
            metadata={
                "category_name": category.name,
                "old_department_id": old_dept_id,
                "new_department_id": new_dept.id,
            },
            ip_address=ip_address,
            user_agent=user_agent,
            commit=False,
        )
    elif changes:
        record_audit_event(
            db=db,
            actor_user_id=actor.id,
            actor_role=actor.role.value,
            action="CATEGORY_UPDATED",
            entity_type="CATEGORY",
            entity_id=str(category.id),
            metadata=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            commit=False,
        )

    db.commit()
    db.refresh(category)

    return CategoryDetailOut(
        id=category.id,
        name=category.name,
        code=category.code,
        description=category.description,
        department_id=category.department_id,
        department=DepartmentOut.model_validate(category.department),
        default_priority=category.default_priority,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
        note=note,
    )


# ── Platform Activity (FR-048, US-ADM-04) ─────────────────────────────────────


def get_platform_activity(db: Session) -> PlatformActivityResponse:
    """
    Aggregate counts by status, by department, total escalations, and 20 recent timeline events (FR-048).
    """
    # 1. Counts by status
    status_counts_raw = db.execute(
        select(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status)
    ).all()

    by_status: dict[str, int] = {s.value: 0 for s in Status}
    for st, count in status_counts_raw:
        val = st.value if hasattr(st, "value") else str(st)
        by_status[val] = count

    # 2. Counts by department
    all_depts = db.scalars(select(Department).order_by(Department.name.asc())).all()
    by_department: list[DepartmentActivityItem] = []

    for dept in all_depts:
        open_count = (
            db.scalar(
                select(func.count(Complaint.id)).where(
                    Complaint.department_id == dept.id,
                    Complaint.status.not_in([Status.RESOLVED, Status.REJECTED]),
                )
            )
            or 0
        )
        escalated_count = (
            db.scalar(
                select(func.count(Complaint.id)).where(
                    Complaint.department_id == dept.id,
                    Complaint.status == Status.ESCALATED,
                )
            )
            or 0
        )
        by_department.append(
            DepartmentActivityItem(
                id=dept.id,
                name=dept.name,
                open=open_count,
                escalated=escalated_count,
            )
        )

    # 3. Total escalations
    escalations_total = (
        db.scalar(select(func.count(Complaint.id)).where(Complaint.status == Status.ESCALATED)) or 0
    )

    # 4. 20 most recent timeline events from ComplaintStatusHistory
    history_rows = db.execute(
        select(
            ComplaintStatusHistory,
            Complaint.complaint_number,
            User.full_name,
        )
        .join(Complaint, Complaint.id == ComplaintStatusHistory.complaint_id)
        .outerjoin(User, User.id == ComplaintStatusHistory.actor_user_id)
        .order_by(
            ComplaintStatusHistory.created_at.desc(),
            ComplaintStatusHistory.id.desc(),
        )
        .limit(20)
    ).all()

    recent_events: list[RecentEventItem] = []
    for h, c_num, actor_name in history_rows:
        recent_events.append(
            RecentEventItem(
                complaint_id=h.complaint_id,
                complaint_number=c_num,
                event_type="STATUS_CHANGE",
                from_status=h.from_status,
                to_status=h.to_status,
                actor=actor_name or ("System" if h.actor_user_id is None else "User"),
                note=h.note,
                created_at=h.created_at,
            )
        )

    return PlatformActivityResponse(
        by_status=by_status,
        by_department=by_department,
        escalations_total=escalations_total,
        escalation_window_minutes=settings.escalation_window_minutes,
        demo_mode=settings.demo_mode,
        recent_events=recent_events,
    )
