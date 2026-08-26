from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.models.database import get_db, PDURecord
from backend.config import settings

router = APIRouter(prefix="/api/pdu", tags=["PDU"])


def _unit_names() -> list[str]:
    hosts = [h.strip() for h in settings.PDU_HOSTS.split(",") if h.strip()]
    return [f"PDU-{i+1}" for i in range(len(hosts))]


def _serialize(record: PDURecord | None) -> dict:
    if not record:
        return {"online": False}
    return {
        "online": True,
        "voltage": record.voltage,
        "current": record.current,
        "power": record.total_power,
        "load_rate": record.load_rate,
        "kwh": record.kwh,
        "alarm": record.alarm,
        "timestamp": record.timestamp,
    }


@router.get("/latest")
async def get_latest(db: AsyncSession = Depends(get_db)):
    units = _unit_names()
    server_units = units[: settings.PDU_SERVER_COUNT]
    tank_cdu_units = units[settings.PDU_SERVER_COUNT :]

    unit_data = {}
    for name in units:
        result = await db.execute(
            select(PDURecord)
            .where(PDURecord.unit == name)
            .order_by(desc(PDURecord.timestamp))
            .limit(1)
        )
        unit_data[name] = _serialize(result.scalar_one_or_none())

    def group_power(names: list[str]) -> float:
        return sum(unit_data[n]["power"] or 0.0 for n in names if unit_data[n]["online"])

    server_power = group_power(server_units)
    tank_cdu_power = group_power(tank_cdu_units)
    online_count = sum(1 for u in unit_data.values() if u["online"])

    return {
        "units": unit_data,
        "server_units": server_units,
        "tank_cdu_units": tank_cdu_units,
        "server_power": server_power,
        "tank_cdu_power": tank_cdu_power,
        "total_power": server_power + tank_cdu_power,
        "online_count": online_count,
        "total_count": len(units),
    }


@router.get("/history")
async def get_history(unit: str = "PDU-1", limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PDURecord)
        .where(PDURecord.unit == unit)
        .order_by(desc(PDURecord.timestamp))
        .limit(limit)
    )
    records = result.scalars().all()
    return [{"power": r.total_power, "timestamp": r.timestamp} for r in records]
