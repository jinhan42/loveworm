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
            "cpu0_status": r.cpu0_status,
            "cpu1_status": r.cpu1_status,
            "psu1_status": r.psu1_status,
            "psu2_status": r.psu2_status,
            "power_capacity_watts": r.power_capacity_watts,
            "accumulated_energy_joules": r.accumulated_energy_joules,
            "power_consumed_watts": r.power_consumed_watts,
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
            "cpu0_status": r.cpu0_status,
            "cpu1_status": r.cpu1_status,
            "psu1_status": r.psu1_status,
            "psu2_status": r.psu2_status,
            "power_consumed_watts": r.power_consumed_watts,
            "timestamp": r.timestamp,
        }
        for r in records
    ]
