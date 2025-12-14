"""
Lottery/Giveaway Campaign API Endpoints
Manage property giveaway campaigns with winner draw
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import random
import secrets

from database import async_session, Tenant, Lead, get_db

router = APIRouter(prefix="/api/tenants", tags=["Lotteries"])
security = HTTPBearer()


# Import auth functions from main
async def verify_tenant_access(
    credentials: HTTPAuthorizationCredentials,
    tenant_id: int,
    db: AsyncSession
) -> Tenant:
    """Verify that the authenticated user has access to the given tenant."""
    import jwt
    from auth_config import JWT_SECRET, JWT_ALGORITHM
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    auth_tenant_id = payload.get("tenant_id")
    
    # Super Admin can access any tenant
    if auth_tenant_id == 0:
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return tenant
    
    # Regular tenant can only access their own data
    if auth_tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return tenant


class LotteryParticipant(BaseModel):
    lead_id: int
    lead_name: str
    phone: Optional[str]
    entry_date: datetime


class Lottery(BaseModel):
    id: Optional[int] = None
    tenant_id: int
    name: str
    description: Optional[str] = None
    prize: str
    start_date: datetime
    end_date: datetime
    status: str = "active"  # active, paused, completed
    winner_id: Optional[int] = None
    participants: List[int] = []  # Lead IDs
    created_at: Optional[datetime] = None


class LotteryResponse(BaseModel):
    id: int
    tenant_id: int
    name: str
    description: Optional[str]
    prize: str
    start_date: datetime
    end_date: datetime
    status: str
    participant_count: int
    winner_id: Optional[int]
    winner_name: Optional[str]
    created_at: datetime


class DrawWinnerResponse(BaseModel):
    lottery_id: int
    winner_id: int
    winner_name: str
    winner_phone: Optional[str]
    total_participants: int


# In-memory storage (replace with database table in production)
LOTTERIES_DB = {}
LOTTERY_ID_COUNTER = 1


@router.get("/{tenant_id}/lotteries", response_model=List[LotteryResponse])
async def get_lotteries(
    tenant_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get all lotteries for a tenant (requires authentication)."""
    # Verify access
    tenant = await verify_tenant_access(credentials, tenant_id, db)
    
    tenant_lotteries = []
    
    for lottery in LOTTERIES_DB.values():
        if lottery["tenant_id"] == tenant_id:
            winner_name = None
            if lottery.get("winner_id"):
                winner_result = await db.execute(
                    select(Lead).where(Lead.id == lottery["winner_id"])
                )
                winner = winner_result.scalar_one_or_none()
                if winner:
                    winner_name = str(winner.name) if winner.name else f"Lead {winner.id}"
            
            tenant_lotteries.append(
                LotteryResponse(
                    id=lottery["id"],
                    tenant_id=lottery["tenant_id"],
                    name=lottery["name"],
                    description=lottery.get("description"),
                    prize=lottery["prize"],
                    start_date=lottery["start_date"],
                    end_date=lottery["end_date"],
                    status=lottery["status"],
                    participant_count=len(lottery.get("participants", [])),
                    winner_id=lottery.get("winner_id"),
                    winner_name=winner_name,
                    created_at=lottery["created_at"]
                )
            )
    
    return tenant_lotteries


@router.post("/{tenant_id}/lotteries", response_model=LotteryResponse)
async def create_lottery(
    tenant_id: int,
    lottery: Lottery,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Create a new lottery campaign (requires authentication)."""
    # Verify access
    tenant = await verify_tenant_access(credentials, tenant_id, db)
    
    global LOTTERY_ID_COUNTER
    
    # Verify tenant exists
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Create lottery
    now = datetime.utcnow()
    lottery_id = LOTTERY_ID_COUNTER
    LOTTERY_ID_COUNTER += 1
    
    lottery_data = {
        "id": lottery_id,
        "tenant_id": tenant_id,
        "name": lottery.name,
        "description": lottery.description,
        "prize": lottery.prize,
        "start_date": lottery.start_date,
        "end_date": lottery.end_date,
        "status": lottery.status,
        "participants": lottery.participants,
        "winner_id": None,
        "created_at": now
    }
    
    LOTTERIES_DB[lottery_id] = lottery_data
    
    return LotteryResponse(
        id=lottery_id,
        tenant_id=tenant_id,
        name=lottery.name,
        description=lottery.description,
        prize=lottery.prize,
        start_date=lottery.start_date,
        end_date=lottery.end_date,
        status=lottery.status,
        participant_count=len(lottery.participants),
        winner_id=None,
        winner_name=None,
        created_at=now
    )


@router.put("/{tenant_id}/lotteries/{lottery_id}", response_model=LotteryResponse)
async def update_lottery(
    tenant_id: int,
    lottery_id: int,
    lottery: Lottery,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Update an existing lottery (requires authentication)."""
    # Verify access
    tenant = await verify_tenant_access(credentials, tenant_id, db)
    
    if lottery_id not in LOTTERIES_DB:
        raise HTTPException(status_code=404, detail="Lottery not found")
    
    existing = LOTTERIES_DB[lottery_id]
    if existing["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update
    LOTTERIES_DB[lottery_id].update({
        "name": lottery.name,
        "description": lottery.description,
        "prize": lottery.prize,
        "start_date": lottery.start_date,
        "end_date": lottery.end_date,
        "status": lottery.status,
        "participants": lottery.participants
    })
    
    updated = LOTTERIES_DB[lottery_id]
    
    winner_name = None
    if updated.get("winner_id"):
        winner_result = await db.execute(
            select(Lead).where(Lead.id == updated["winner_id"])
        )
        winner = winner_result.scalar_one_or_none()
        if winner:
            winner_name = winner.name or f"Lead {winner.id}"
    
    return LotteryResponse(
        id=lottery_id,
        tenant_id=tenant_id,
        name=updated["name"],
        description=updated.get("description"),
        prize=updated["prize"],
        start_date=updated["start_date"],
        end_date=updated["end_date"],
        status=updated["status"],
        participant_count=len(updated.get("participants", [])),
        winner_id=updated.get("winner_id"),
        winner_name=winner_name,
        created_at=updated["created_at"]
    )


@router.delete("/{tenant_id}/lotteries/{lottery_id}")
async def delete_lottery(
    tenant_id: int,
    lottery_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a lottery (requires authentication)."""
    # Verify access (no db needed for delete)
    import jwt
    from auth_config import JWT_SECRET, JWT_ALGORITHM
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    auth_tenant_id = payload.get("tenant_id")
    if auth_tenant_id != 0 and auth_tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if lottery_id not in LOTTERIES_DB:
        raise HTTPException(status_code=404, detail="Lottery not found")
    
    existing = LOTTERIES_DB[lottery_id]
    if existing["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    del LOTTERIES_DB[lottery_id]
    
    return {"status": "deleted", "id": lottery_id}


@router.post("/{tenant_id}/lotteries/{lottery_id}/draw", response_model=DrawWinnerResponse)
async def draw_winner(
    tenant_id: int,
    lottery_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Randomly draw a winner from lottery participants (requires authentication)."""
    # Verify access
    tenant = await verify_tenant_access(credentials, tenant_id, db)
    
    if lottery_id not in LOTTERIES_DB:
        raise HTTPException(status_code=404, detail="Lottery not found")
    
    lottery = LOTTERIES_DB[lottery_id]
    if lottery["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not lottery.get("participants"):
        raise HTTPException(status_code=400, detail="No participants in lottery")
    
    if lottery.get("winner_id"):
        raise HTTPException(status_code=400, detail="Winner already drawn")
    
    # Cryptographically secure random draw
    winner_id = secrets.choice(lottery["participants"])
    
    # Fetch winner details
    winner_result = await db.execute(
        select(Lead).where(Lead.id == winner_id)
    )
    winner = winner_result.scalar_one_or_none()
    
    if not winner:
        raise HTTPException(status_code=404, detail="Winner lead not found")
    
    # Update lottery
    LOTTERIES_DB[lottery_id]["winner_id"] = winner_id
    LOTTERIES_DB[lottery_id]["status"] = "completed"
    
    return DrawWinnerResponse(
        lottery_id=lottery_id,
        winner_id=winner_id,
        winner_name=str(winner.name) if winner.name else f"Lead {winner.id}",
        winner_phone=str(winner.phone) if winner.phone else None,
        total_participants=len(lottery["participants"])
    )


@router.patch("/{tenant_id}/lotteries/{lottery_id}/status")
async def update_lottery_status(
    tenant_id: int,
    lottery_id: int,
    status: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update lottery status - active/paused/completed (requires authentication)."""
    # Verify access
    import jwt
    from auth_config import JWT_SECRET, JWT_ALGORITHM
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    auth_tenant_id = payload.get("tenant_id")
    if auth_tenant_id != 0 and auth_tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if lottery_id not in LOTTERIES_DB:
        raise HTTPException(status_code=404, detail="Lottery not found")
    
    lottery = LOTTERIES_DB[lottery_id]
    if lottery["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if status not in ["active", "paused", "completed"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    LOTTERIES_DB[lottery_id]["status"] = status
    
    return {"status": "updated", "lottery_id": lottery_id, "new_status": status}
