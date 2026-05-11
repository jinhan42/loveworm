from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.models.database import get_db, HeatExchangerRecord

router = APIRouter(prefix="/api/heat-exchanger", tags=["열교환기"])

@router.get("/latest")
async def get_latest(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HeatExchangerRecord).order_by(desc(HeatExchangerRecord.timestamp)).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {}
    return {"water_lpm": record.water_lpm, "oil_lpm": record.oil_lpm, "timestamp": record.timestamp}

@router.get("/history")
async def get_history(limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(HeatExchangerRecord).order_by(desc(HeatExchangerRecord.timestamp)).limit(limit)
    )
    records = result.scalars().all()
    return [{"water_lpm": r.water_lpm, "oil_lpm": r.oil_lpm, "timestamp": r.timestamp} for r in records]
