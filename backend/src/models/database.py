"""SQLAlchemy setup — engine, session factory, declarative base.

Table models (``beneficiaries``, ``visits`` — Implementation Plan Appendix B)
are declared in Hour 1, task 5 together with Alembic migrations. This module
only provides the connection plumbing.

``DATABASE_URL`` selects the backend:

- default: SQLite (offline demo, zero setup — blueprint Part 11)
- example: ``postgresql+psycopg2://user:pass@localhost:5432/prahari``
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./prahari.db")

# check_same_thread=False is required for SQLite under FastAPI's threadpool.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Declarative base for all ORM models (beneficiaries, visits, ...)."""
