import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# ============================================================
# Database configuration
# ============================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./forgeai.db",
)


# ============================================================
# SQLite configuration
# ============================================================

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
    }


# ============================================================
# Engine
# ============================================================

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)


# ============================================================
# Session
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# ============================================================
# ORM base
# ============================================================

class Base(DeclarativeBase):
    pass


# ============================================================
# Database initialization
# ============================================================

def init_db() -> None:
    """
    Create all registered database tables.

    Models must be imported before this function is called so
    SQLAlchemy knows about them.
    """

    from src.db.models import Task  # noqa: F401

    Base.metadata.create_all(
        bind=engine
    )