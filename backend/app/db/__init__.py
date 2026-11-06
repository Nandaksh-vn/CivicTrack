"""CivicTrack — db package"""

# Import all models here so Alembic autogenerate discovers them
import app.models  # noqa: F401
from app.db.base import Base  # noqa: F401
