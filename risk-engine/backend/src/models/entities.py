"""ORM entities — PostgreSQL schema from Implementation Plan Appendix B.

Tables: ``beneficiaries`` and ``visits`` (append-only screening history).
The types are portable: ``Uuid`` renders as native UUID on PostgreSQL and as
CHAR(32) on the SQLite dev/demo backend; JSONB on PostgreSQL, JSON elsewhere.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.database import Base

# JSONB on PostgreSQL, generic JSON elsewhere (SQLite dev/demo).
JSONType = JSON().with_variant(JSONB, "postgresql")


class Beneficiary(Base):
    """A registered beneficiary (child or pregnant woman)."""

    __tablename__ = "beneficiaries"

    id: Mapped[str] = mapped_column(String, primary_key=True, comment="e.g. B001")
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    age_months: Mapped[int] = mapped_column(Integer, nullable=False)
    sex: Mapped[str] = mapped_column(String(10), nullable=False, comment="male | female")
    pregnancy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    visits: Mapped[list["Visit"]] = relationship(
        back_populates="beneficiary",
        cascade="all, delete-orphan",
        order_by="Visit.visit_date",
    )


class Visit(Base):
    """One screening visit — append-only, the basis of the trajectory engine."""

    __tablename__ = "visits"
    __table_args__ = (
        Index("idx_visits_beneficiary_date", "beneficiary_id", "visit_date"),
    )

    # Appendix B: id UUID PRIMARY KEY DEFAULT gen_random_uuid(). The Python-side
    # default is portable; gen_random_uuid() is a PostgreSQL-only server default.
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    beneficiary_id: Mapped[str] = mapped_column(
        String, ForeignKey("beneficiaries.id"), nullable=False, index=True
    )
    visit_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Anthropometry inputs + derived z-scores.
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    muac_mm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    whz: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    haz: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    waz: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    muac_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    whz_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    haz_category: Mapped[str | None] = mapped_column(String(20), nullable=True)
    waz_category: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # CV-pipeline input (AI team's classifier output).
    anemia_ai_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    anemia_ai_confidence: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)

    # Final screening output (Appendix A response shape).
    anemia_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nutrition_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    overall_priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    trajectory: Mapped[str | None] = mapped_column(String(30), nullable=True)
    contributors: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(String(50), nullable=True)
    safety_flags: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    escalated: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    context_snapshot: Mapped[dict | None] = mapped_column(JSONType, nullable=True)

    beneficiary: Mapped[Beneficiary] = relationship(back_populates="visits")
