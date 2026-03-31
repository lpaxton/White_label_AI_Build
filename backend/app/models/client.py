"""
Client onboarding models for the White-Label AI advisory platform.
SQLAlchemy 2.0 async-compatible models.
"""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ── Base ────────────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Enums ───────────────────────────────────────────────────────────────────────

class ClientStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    KYC_PENDING = "KYC_PENDING"
    AGREEMENT_SENT = "AGREEMENT_SENT"
    SIGNED = "SIGNED"
    ACTIVE = "ACTIVE"


class ClientTier(str, enum.Enum):
    ESSENTIAL = "ESSENTIAL"
    GROWTH = "GROWTH"
    PREMIUM = "PREMIUM"
    ELITE = "ELITE"


class RiskBand(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    AGGRESSIVE = "AGGRESSIVE"


# ── Association table (Household ↔ Client many-to-many) ─────────────────────────

household_clients = Table(
    "household_clients",
    Base.metadata,
    Column("household_id", UUID(as_uuid=True), ForeignKey("households.id", ondelete="CASCADE"), primary_key=True),
    Column("client_id", UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), primary_key=True),
)


# ── Client ──────────────────────────────────────────────────────────────────────

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    firm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    advisor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Status & tier
    status: Mapped[ClientStatus] = mapped_column(
        Enum(ClientStatus, name="client_status", native_enum=False),
        default=ClientStatus.DRAFT,
        nullable=False,
    )
    tier: Mapped[ClientTier] = mapped_column(
        Enum(ClientTier, name="client_tier", native_enum=False),
        nullable=True,
    )
    tier_assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # PII
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(nullable=True)
    ssn_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Address
    address_street: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address_state: Mapped[str | None] = mapped_column(String(2), nullable=True)
    address_zip: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Employment & income
    employment_status: Mapped[str | None] = mapped_column(String(60), nullable=True)
    annual_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    tax_filing_status: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Consent
    ai_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    risk_profile: Mapped["RiskProfile | None"] = relationship(
        back_populates="client", uselist=False, cascade="all, delete-orphan"
    )
    kyc_documents: Mapped[list["KYCDocument"]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    households: Mapped[list["Household"]] = relationship(
        secondary=household_clients, back_populates="clients"
    )


# ── RiskProfile ─────────────────────────────────────────────────────────────────

class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    band: Mapped[RiskBand] = mapped_column(
        Enum(RiskBand, name="risk_band", native_enum=False), nullable=False
    )
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    client: Mapped["Client"] = relationship(back_populates="risk_profile")


# ── Household ───────────────────────────────────────────────────────────────────

class Household(Base):
    __tablename__ = "households"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    firm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    primary_client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    clients: Mapped[list["Client"]] = relationship(
        secondary=household_clients, back_populates="households"
    )


# ── KYCDocument ─────────────────────────────────────────────────────────────────

class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(String(60), nullable=False)
    blob_key: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    client: Mapped["Client"] = relationship(back_populates="kyc_documents")
