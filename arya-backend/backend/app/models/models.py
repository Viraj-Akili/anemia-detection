from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    JSON,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

JSONType = JSON().with_variant(JSONB, "postgresql")


class UserRole(str, PyEnum):
    WORKER = "WORKER"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"


class BeneficiaryCategory(str, PyEnum):
    CHILD = "CHILD"
    PREGNANT_WOMAN = "PREGNANT_WOMAN"


class Sex(str, PyEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class ScreeningStatus(str, PyEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"


class RiskLevel(str, PyEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FollowUpStatus(str, PyEnum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.WORKER)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    beneficiaries: Mapped[list["Beneficiary"]] = relationship(
        back_populates="created_by_user"
    )
    screenings: Mapped[list["Screening"]] = relationship(
        back_populates="worker"
    )
    followups: Mapped[list["FollowUp"]] = relationship(
        back_populates="assigned_user"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    date_of_birth: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    sex: Mapped[Sex] = mapped_column(Enum(Sex), nullable=False)
    category: Mapped[BeneficiaryCategory] = mapped_column(Enum(BeneficiaryCategory), nullable=False, index=True)
    is_pregnant: Mapped[bool] = mapped_column(default=False, nullable=False)
    trimester: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    created_by_user: Mapped["User"] = relationship(back_populates="beneficiaries")
    screenings: Mapped[list["Screening"]] = relationship(
        back_populates="beneficiary", cascade="all, delete-orphan", order_by="Screening.started_at.desc()"
    )
    followups: Mapped[list["FollowUp"]] = relationship(
        back_populates="beneficiary", cascade="all, delete-orphan", order_by="FollowUp.due_date.desc()"
    )

    __table_args__ = (
        Index("ix_beneficiaries_category_dob", "category", "date_of_birth"),
    )

    def __repr__(self) -> str:
        return f"<Beneficiary(id={self.id}, name='{self.name}', category='{self.category}')>"


class Screening(Base):
    __tablename__ = "screenings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    beneficiary_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    worker_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    status: Mapped[ScreeningStatus] = mapped_column(
        Enum(ScreeningStatus), nullable=False, default=ScreeningStatus.IN_PROGRESS, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    beneficiary: Mapped["Beneficiary"] = relationship(back_populates="screenings")
    worker: Mapped["User"] = relationship(back_populates="screenings")
    measurements: Mapped[list["Measurement"]] = relationship(
        back_populates="screening", cascade="all, delete-orphan", order_by="Measurement.created_at"
    )
    result: Mapped[Optional["Result"]] = relationship(
        back_populates="screening", cascade="all, delete-orphan", uselist=False
    )
    followups: Mapped[list["FollowUp"]] = relationship(
        back_populates="screening"
    )

    __table_args__ = (
        Index("ix_screenings_beneficiary_started", "beneficiary_id", "started_at"),
    )

    def __repr__(self) -> str:
        return f"<Screening(id={self.id}, beneficiary_id={self.beneficiary_id}, status='{self.status}')>"


class Measurement(Base):
    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    screening_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("screenings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    weight_kg: Mapped[Optional[float]] = mapped_column(nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column(nullable=True)
    muac_mm: Mapped[Optional[float]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    screening: Mapped["Screening"] = relationship(back_populates="measurements")

    def __repr__(self) -> str:
        return f"<Measurement(id={self.id}, screening_id={self.screening_id}, weight_kg={self.weight_kg}, height_cm={self.height_cm}, muac_mm={self.muac_mm})>"


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    screening_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("screenings.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    anemia_risk: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False, index=True)
    nutrition_risk: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False, index=True)
    overall_priority: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False, index=True)
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    trajectory: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contributors: Mapped[Optional[dict]] = mapped_column(JSONType, nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    screening: Mapped["Screening"] = relationship(back_populates="result")

    def __repr__(self) -> str:
        return f"<Result(id={self.id}, screening_id={self.screening_id}, anemia_risk='{self.anemia_risk}', nutrition_risk='{self.nutrition_risk}', overall_priority='{self.overall_priority}')>"


class FollowUp(Base):
    __tablename__ = "followups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    beneficiary_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("beneficiaries.id", ondelete="CASCADE"), nullable=False, index=True
    )
    screening_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("screenings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assigned_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    status: Mapped[FollowUpStatus] = mapped_column(
        Enum(FollowUpStatus), nullable=False, default=FollowUpStatus.PENDING, index=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    beneficiary: Mapped["Beneficiary"] = relationship(back_populates="followups")
    screening: Mapped[Optional["Screening"]] = relationship(back_populates="followups")
    assigned_user: Mapped["User"] = relationship(back_populates="followups")

    __table_args__ = (
        Index("ix_followups_beneficiary_due", "beneficiary_id", "due_date"),
        Index("ix_followups_status_due", "status", "due_date"),
    )

    def __repr__(self) -> str:
        return f"<FollowUp(id={self.id}, beneficiary_id={self.beneficiary_id}, status='{self.status}', due_date='{self.due_date}')>"