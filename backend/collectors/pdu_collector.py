"""
PDU 수집기 - DEFOG KC10-20ELPM SNMP 폴링 (3대: 서버용 + TANK+CDU용)
"""
import logging

from backend.config import settings
from backend.models.database import AsyncSessionLocal, PDURecord
from backend.collectors.defog_pdu import poll_many

logger = logging.getLogger(__name__)


def _pdu_map() -> dict:
    hosts = [h.strip() for h in settings.PDU_HOSTS.split(",") if h.strip()]
    return {f"PDU-{i+1}": ip for i, ip in enumerate(hosts)}


async def collect_pdu():
    pdus = _pdu_map()
    if not pdus:
        return

    results = await poll_many(
        pdus, community=settings.PDU_SNMP_COMMUNITY, timeout=2, retries=1
    )

    async with AsyncSessionLocal() as session:
        for unit, entry in results.items():
            values = entry["values"]
            if not values:
                logger.error(f"PDU SNMP 오류 ({unit}): {entry['error']}")
                continue
            session.add(PDURecord(
                unit=unit,
                voltage=values.get("voltage"),
                current=values.get("current"),
                power_factor=None,
                total_power=values.get("power"),
                load_rate=values.get("load_rate"),
                kwh=values.get("kwh"),
                alarm=values.get("alarm"),
            ))
        await session.commit()

    online = [u for u, e in results.items() if e["values"]]
    logger.info(f"PDU 수집 완료 - 연결됨: {online}")
