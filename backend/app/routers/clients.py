"""
Client onboarding API router.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user
from app.schemas.client import (
    ClientCreate,
    ClientRead,
    ClientUpdate,
    RiskProfileCreate,
    RiskProfileRead,
)
from app.services import client as client_svc

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: ClientCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClientRead:
    client = await client_svc.create_client(
        db,
        data=body,
        advisor_id=user["advisor_id"],
        firm_id=user["firm_id"],
    )
    return ClientRead.model_validate(client)


@router.get("", response_model=list[ClientRead])
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ClientRead]:
    clients = await client_svc.get_clients(db, advisor_id=user["advisor_id"], skip=skip, limit=limit)
    return [ClientRead.model_validate(c) for c in clients]


@router.get("/{client_id}", response_model=ClientRead)
async def get_client(
    client_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClientRead:
    client = await client_svc.get_client(db, client_id=client_id, advisor_id=user["advisor_id"])
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientRead.model_validate(client)


@router.patch("/{client_id}", response_model=ClientRead)
async def update_client(
    client_id: UUID,
    body: ClientUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClientRead:
    client = await client_svc.update_client(
        db, client_id=client_id, advisor_id=user["advisor_id"], data=body
    )
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientRead.model_validate(client)


@router.post("/{client_id}/risk-profile", response_model=RiskProfileRead, status_code=status.HTTP_201_CREATED)
async def create_risk_profile(
    client_id: UUID,
    body: RiskProfileCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskProfileRead:
    # Verify the client belongs to this advisor
    client = await client_svc.get_client(db, client_id=client_id, advisor_id=user["advisor_id"])
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    profile = await client_svc.create_risk_profile(db, client_id=client_id, answers=body.answers)
    return RiskProfileRead.model_validate(profile)


@router.get("/{client_id}/risk-profile", response_model=RiskProfileRead)
async def get_risk_profile(
    client_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskProfileRead:
    # Verify the client belongs to this advisor
    client = await client_svc.get_client(db, client_id=client_id, advisor_id=user["advisor_id"])
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")

    profile = await client_svc.get_risk_profile(db, client_id=client_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Risk profile not found")
    return RiskProfileRead.model_validate(profile)
