"""Shared API dependencies — DB sessions, beneficiary resolution, logging.

- ``get_db``: yields a SQLAlchemy session (closed on teardown).
- ``get_beneficiary``: resolves a beneficiary record or raises 404 (Hour 8).
- Request logging (beneficiary_id, latency, risk bands — never raw PII)
  is added when the analyze route is wired in Hour 8.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_beneficiary(beneficiary_id: str) -> None:
    """Placeholder for beneficiary resolution (Hour 8 / Hour 9 CRUD).

    Raises 404 for unknown beneficiaries; the real lookup queries the
    ``beneficiaries`` table once the ORM models exist.
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Unknown beneficiary: {beneficiary_id}",
    )
