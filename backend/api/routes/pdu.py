import json
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.models.database import get_db, PDURecord

router = APIRouter(prefix="/api/pdu", tags=["PDU"])

@router.get("/latest")
async def get_latest(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PDURecord).order_by(desc(PDURecord.timestamp)).limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {}
    return {
        "total_power": record.total_power,
        "outlets": json.loads(record.outlet_data or "{}"),
        "timestamp": record.timestamp
    }

@router.get("/history")
async def get_history(limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PDURecord).order_by(desc(PDURecord.timestamp)).limit(limit)
    )
    records = result.scalars().all()
    return [{"total_power": r.total_power, "timestamp": r.timestamp} for r in records]
