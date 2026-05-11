from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.models.database import get_db, BMCRecord

router = APIRouter(prefix="/api/bmc", tags=["BMC"])

@router.get("/latest")
async def get_latest_bmc(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BMCRecord).order_by(desc(BMCRecord.timestamp)).limit(20)
    )
    records = result.scalars().all()
    return [
        {
            "host": r.host,
            "cpu_temp": r.cpu_temp,
            "psu_power": r.psu_power,
            "psu_voltage": r.psu_voltage,
            "psu_current": r.psu_current,
            "timestamp": r.timestamp,
        }
        for r in records
    ]

@router.get("/history/{host}")
async def get_bmc_history(host: str, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BMCRecord)
        .where(BMCRecord.host == host)
        .order_by(desc(BMCRecord.timestamp))
        .limit(limit)
    )
    records = result.scalars().all()
    return [
        {
            "cpu_temp": r.cpu_temp,
            "psu_power": r.psu_power,
            "timestamp": r.timestamp,
        }
        for r in records
    ]
