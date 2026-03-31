"""
Pydantic schemas for Client onboarding API.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, computed_field


# ── Client ──────────────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    date_of_birth: date | None = None
    ssn: str | None = Field(default=None, description="Plain text SSN — encrypted at the service layer")
    address_street: str | None = Field(default=None, max_length=255)
    address_city: str | None = Field(default=None, max_length=120)
    address_state: str | None = Field(default=None, max_length=2)
    address_zip: str | None = Field(default=None, max_length=10)
    employment_status: str | None = Field(default=None, max_length=60)
    annual_income: float | None = None
    tax_filing_status: str | None = Field(default=None, max_length=40)
    ai_consent: bool = False


class ClientRead(BaseModel):
    id: UUID
    firm_id: UUID
    advisor_id: UUID
    status: str
    tier: str | None
    first_name: str
    last_name: str
    email: str
    phone: str | None
    date_of_birth: date | None
    address_street: str | None
    address_city: str | None
    address_state: str | None
    address_zip: str | None
    employment_status: str | None
    annual_income: float | None
    tax_filing_status: str | None
    ai_consent: bool
    tier_assigned_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    model_config = {"from_attributes": True}


class ClientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    ssn: str | None = Field(default=None, description="Plain text SSN — re-encrypted at the service layer")
    address_street: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_zip: str | None = None
    employment_status: str | None = None
    annual_income: float | None = None
    tax_filing_status: str | None = None
    ai_consent: bool | None = None
    status: str | None = None
    tier: str | None = None


# ── RiskProfile ─────────────────────────────────────────────────────────────────

class RiskProfileCreate(BaseModel):
    answers: list[int] = Field(min_length=10, max_length=10, description="10 answers on a 1-5 scale")


class RiskProfileRead(BaseModel):
    id: UUID
    client_id: UUID
    score: int
    band: str
    answers: dict
    scored_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Household ───────────────────────────────────────────────────────────────────

class HouseholdCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    primary_client_id: UUID | None = None
    client_ids: list[UUID] = Field(default_factory=list)


class HouseholdRead(BaseModel):
    id: UUID
    firm_id: UUID
    name: str
    primary_client_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}
