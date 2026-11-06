"""
CivicTrack — Pytest configuration and shared fixtures
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import Priority, Role, Status
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# In-memory SQLite engine with StaticPool so all connections share the same memory DB
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator[None, None, None]:
    """Create all schema tables once for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Yield an isolated database session rolled back after every test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient with the get_db dependency overridden to use the test session."""

    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ── Sample Data Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def dept_roads(db: Session) -> Department:
    dept = Department(
        name="Road Maintenance",
        code="ROADS",
        description="Potholes and road repairs",
        is_active=True,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@pytest.fixture
def dept_electrical(db: Session) -> Department:
    dept = Department(
        name="Electrical Department",
        code="ELECTRICAL",
        description="Streetlights and wiring",
        is_active=True,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@pytest.fixture
def cat_pothole(db: Session, dept_roads: Department) -> ComplaintCategory:
    cat = ComplaintCategory(
        name="Pothole / Damaged Road",
        code="POTHOLE",
        department_id=dept_roads.id,
        default_priority=Priority.MEDIUM,
        is_active=True,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@pytest.fixture
def cat_streetlight(db: Session, dept_electrical: Department) -> ComplaintCategory:
    cat = ComplaintCategory(
        name="Broken Streetlight",
        code="STREETLIGHT",
        department_id=dept_electrical.id,
        default_priority=Priority.MEDIUM,
        is_active=True,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@pytest.fixture
def admin_user(db: Session) -> tuple[User, str]:
    user = User(
        full_name="Platform Admin",
        email="admin@demo.local",
        password_hash=hash_password("DemoAdmin123"),
        role=Role.PLATFORM_ADMIN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token, _ = create_access_token(user.id, user.role.value)
    return user, token


@pytest.fixture
def citizen_user(db: Session) -> tuple[User, str]:
    user = User(
        full_name="Citizen One",
        email="citizen@demo.local",
        password_hash=hash_password("Citizen123"),
        role=Role.CITIZEN,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token, _ = create_access_token(user.id, user.role.value)
    return user, token


@pytest.fixture
def officer_roads(db: Session, dept_roads: Department) -> tuple[User, str]:
    user = User(
        full_name="Roads Officer",
        email="roads@demo.local",
        password_hash=hash_password("RoadsOfficer123"),
        role=Role.DEPARTMENT_OFFICER,
        department_id=dept_roads.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token, _ = create_access_token(user.id, user.role.value, user.department_id)
    return user, token


@pytest.fixture
def officer_electrical(db: Session, dept_electrical: Department) -> tuple[User, str]:
    user = User(
        full_name="Electrical Officer",
        email="electrical@demo.local",
        password_hash=hash_password("ElectricalOfficer123"),
        role=Role.DEPARTMENT_OFFICER,
        department_id=dept_electrical.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token, _ = create_access_token(user.id, user.role.value, user.department_id)
    return user, token


@pytest.fixture
def superintendent_user(db: Session) -> tuple[User, str]:
    user = User(
        full_name="Superintendent Officer",
        email="superintendent@demo.local",
        password_hash=hash_password("Superintendent123"),
        role=Role.SUPERINTENDENT_OFFICER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token, _ = create_access_token(user.id, user.role.value)
    return user, token


@pytest.fixture
def complaint_roads(
    db: Session,
    citizen_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
) -> Complaint:
    citizen, _ = citizen_user
    complaint = Complaint(
        complaint_number="CT-2026-000001",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole on Main Road",
        description="Dangerous pothole near the bus stand.",
        status=Status.PENDING_DEPARTMENT_REVIEW,
        priority=Priority.HIGH,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@pytest.fixture
def complaint_electrical(
    db: Session,
    citizen_user: tuple[User, str],
    cat_streetlight: ComplaintCategory,
    dept_electrical: Department,
) -> Complaint:
    citizen, _ = citizen_user
    complaint = Complaint(
        complaint_number="CT-2026-000002",
        citizen_id=citizen.id,
        category_id=cat_streetlight.id,
        department_id=dept_electrical.id,
        title="Broken Streetlight",
        description="Streetlight flickering and dim.",
        status=Status.ACCEPTED,
        priority=Priority.MEDIUM,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@pytest.fixture
def escalated_complaint(
    db: Session,
    citizen_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
) -> Complaint:
    citizen, _ = citizen_user
    complaint = Complaint(
        complaint_number="CT-2026-000003",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Escalated Pothole",
        description="Overdue pothole complaint.",
        status=Status.ESCALATED,
        priority=Priority.HIGH,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint
