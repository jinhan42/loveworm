import asyncio
import httpx
from backend.config import settings
from backend.models.database import AsyncSessionLocal, BMCRecord
import logging

logger = logging.getLogger(__name__)

async def collect_via_redfish(host: str) -> dict:
    base = f"https://{host}/redfish/v1/Chassis/Self"
    auth = (settings.BMC_USERNAME, settings.BMC_PASSWORD)
    result = {}
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            # 온도/팬 데이터 (액침냉각 서버는 대부분 Absent)
            thermal_r = await client.get(f"{base}/Thermal", auth=auth)
            thermal = thermal_r.json()

            # 전력 데이터
            power_r = await client.get(f"{base}/Power", auth=auth)
            power = power_r.json()

            # PSU 상태
            psus = power.get("PowerSupplies", [])
            result["psu1_status"] = psus[0].get("Status", {}).get("Health", "Absent") if len(psus) > 0 else "Absent"
            result["psu2_status"] = psus[1].get("Status", {}).get("Health", "Absent") if len(psus) > 1 else "Absent"

            # PSU State가 Absent면 Absent로 표시
            if len(psus) > 0 and psus[0].get("Status", {}).get("State") == "Absent":
                result["psu1_status"] = "Absent"
            if len(psus) > 1 and psus[1].get("Status", {}).get("State") == "Absent":
                result["psu2_status"] = "Absent"

            # 전력 제어 데이터
            power_controls = power.get("PowerControl", [])
            if power_controls:
                pc = power_controls[0]
                result["power_capacity_watts"] = pc.get("PowerCapacityWatts")
                result["power_consumed_watts"] = pc.get("PowerConsumedWatts")
                oem = pc.get("Oem", {}).get("Vendor", {})
                result["accumulated_energy_joules"] = oem.get("PowerMetrics", {}).get("AccumulatedEnergyJoules")

        # CPU 상태 (Systems 엔드포인트)
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            cpu0_r = await client.get(f"https://{host}/redfish/v1/Systems/Self/Processors/CPU0", auth=auth)
            cpu0 = cpu0_r.json()
            result["cpu0_status"] = cpu0.get("Status", {}).get("Health", "Unknown")

            cpu1_r = await client.get(f"https://{host}/redfish/v1/Systems/Self/Processors/CPU1", auth=auth)
            cpu1 = cpu1_r.json()
            result["cpu1_status"] = cpu1.get("Status", {}).get("Health", "Unknown")

    except Exception as e:
        logger.error(f"Redfish 오류 [{host}]: {e}")

    return result

async def collect_bmc():
    hosts = [h.strip() for h in settings.BMC_HOSTS.split(",")]
    async with AsyncSessionLocal() as session:
        for host in hosts:
            data = {}
            if settings.BMC_USE_REDFISH:
                data = await collect_via_redfish(host)

            if data:
                record = BMCRecord(
                    host=host,
                    cpu0_status=data.get("cpu0_status", "Unknown"),
                    cpu1_status=data.get("cpu1_status", "Unknown"),
                    psu1_status=data.get("psu1_status", "Unknown"),
                    psu2_status=data.get("psu2_status", "Unknown"),
                    power_capacity_watts=data.get("power_capacity_watts"),
                    accumulated_energy_joules=data.get("accumulated_energy_joules"),
                    power_consumed_watts=data.get("power_consumed_watts"),
                )
                session.add(record)
                logger.info(f"BMC [{host}] 수집 완료 - CPU0:{data.get('cpu0_status')} CPU1:{data.get('cpu1_status')}")
            else:
                logger.warning(f"BMC [{host}] 데이터 없음")

        await session.commit()
