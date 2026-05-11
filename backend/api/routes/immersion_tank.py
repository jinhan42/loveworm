from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.models.database import get_db, ImmersionTankRecord

router = APIRouter(prefix="/api/immersion-tank", tags=["이머전탱크"])

@router.get("/latest")
async def get_latest(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ImmersionTankRecord).order_by(desc(ImmersionTankRecord.timestamp)).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {}
    return {
        "temp_upper":  record.temp_upper,
        "temp_lower":  record.temp_lower,
        "flow_upper":  record.flow_upper,
        "flow_lower":  record.flow_lower,
        "timestamp":   record.timestamp
    }

@router.get("/history")
async def get_history(limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ImmersionTankRecord).order_by(desc(ImmersionTankRecord.timestamp)).limit(limit)
    )
    records = result.scalars().all()
    return [
        {
            "temp_upper": r.temp_upper,
            "temp_lower": r.temp_lower,
            "flow_upper": r.flow_upper,
            "flow_lower": r.flow_lower,
            "timestamp":  r.timestamp
        }
        for r in records
    ]
