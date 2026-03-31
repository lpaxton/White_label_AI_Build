"""
Client service — business logic for onboarding, encryption, risk scoring, tier assignment.
"""

from datetime import datetime, timezone
from uuid import UUID

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.client import Client, ClientStatus, ClientTier, RiskBand, RiskProfile
from app.schemas.client import ClientCreate, ClientUpdate

# ── SSN encryption ──────────────────────────────────────────────────────────────

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        if not settings.FERNET_KEY:
            raise ValueError("FERNET_KEY is not configured")
        _fernet = Fernet(settings.FERNET_KEY.encode())
    return _fernet


def encrypt_ssn(ssn: str) -> str:
    return _get_fernet().encrypt(ssn.encode()).decode()


def decrypt_ssn(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


# ── Risk scoring ────────────────────────────────────────────────────────────────

# Weights per question (index 0-9). Sum of weights = 1.0
RISK_WEIGHTS = [0.15, 0.15, 0.12, 0.10, 0.10, 0.08, 0.08, 0.08, 0.07, 0.07]


def score_risk_profile(answers: list[int]) -> tuple[int, str]:
    """
    Score 10 answers (each 1-5) using weighted scoring.
    Returns (score, band).
    Band thresholds: LOW < 25, MODERATE 25-35, AGGRESSIVE > 35.
    """
    if len(answers) != 10:
        raise ValueError("Exactly 10 answers required")

    raw = sum(a * w for a, w in zip(answers, RISK_WEIGHTS))
    score = round(raw * 10)  # scale to 0-50 range

    if score < 25:
        band = RiskBand.LOW.value
    elif score <= 35:
        band = RiskBand.MODERATE.value
    else:
        band = RiskBand.AGGRESSIVE.value

    return score, band


# ── Tier assignment ─────────────────────────────────────────────────────────────

def assign_tier(aum: float) -> str:
    """
    Assign client tier based on assets under management.
    ESSENTIAL < 250k, GROWTH < 1M, PREMIUM < 5M, ELITE >= 5M.
    """
    if aum < 250_000:
        return ClientTier.ESSENTIAL.value
    if aum < 1_000_000:
        return ClientTier.GROWTH.value
    if aum < 5_000_000:
        return ClientTier.PREMIUM.value
    return ClientTier.ELITE.value


# ── CRUD ────────────────────────────────────────────────────────────────────────

async def create_client(
    db: AsyncSession,
    data: ClientCreate,
    advisor_id: UUID,
    firm_id: UUID,
) -> Client:
    client = Client(
        firm_id=firm_id,
        advisor_id=advisor_id,
        status=ClientStatus.DRAFT,
        tier=ClientTier.ESSENTIAL,
        tier_assigned_at=datetime.now(timezone.utc),
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        date_of_birth=data.date_of_birth,
        ssn_encrypted=encrypt_ssn(data.ssn) if data.ssn else None,
        address_street=data.address_street,
        address_city=data.address_city,
        address_state=data.address_state,
        address_zip=data.address_zip,
        employment_status=data.employment_status,
        annual_income=data.annual_income,
        tax_filing_status=data.tax_filing_status,
        ai_consent=data.ai_consent,
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


async def get_clients(
    db: AsyncSession,
    advisor_id: UUID,
    skip: int = 0,
    limit: int = 50,
) -> list[Client]:
    result = await db.execute(
        select(Client)
        .where(Client.advisor_id == advisor_id)
        .order_by(Client.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_client(
    db: AsyncSession,
    client_id: UUID,
    advisor_id: UUID,
) -> Client | None:
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.advisor_id == advisor_id)
    )
    return result.scalar_one_or_none()


async def update_client(
    db: AsyncSession,
    client_id: UUID,
    advisor_id: UUID,
    data: ClientUpdate,
) -> Client | None:
    client = await get_client(db, client_id, advisor_id)
    if client is None:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # Handle SSN re-encryption
    if "ssn" in update_data:
        ssn_plain = update_data.pop("ssn")
        if ssn_plain is not None:
            update_data["ssn_encrypted"] = encrypt_ssn(ssn_plain)

    for field, value in update_data.items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)
    return client


async def create_risk_profile(
    db: AsyncSession,
    client_id: UUID,
    answers: list[int],
) -> RiskProfile:
    score, band = score_risk_profile(answers)
    profile = RiskProfile(
        client_id=client_id,
        score=score,
        band=band,
        answers={"raw": answers},
        scored_at=datetime.now(timezone.utc),
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_risk_profile(
    db: AsyncSession,
    client_id: UUID,
) -> RiskProfile | None:
    result = await db.execute(
        select(RiskProfile).where(RiskProfile.client_id == client_id)
    )
    return result.scalar_one_or_none()
