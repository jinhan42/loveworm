import asyncio
import httpx
from pyghmi.ipmi import command as ipmi_command
from backend.config import settings
from backend.models.database import AsyncSessionLocal, BMCRecord
import logging

logger = logging.getLogger(__name__)

async def collect_via_redfish(host: str) -> dict:
    url = f"https://{host}/redfish/v1/Chassis/1/Thermal"
    auth = (settings.BMC_USERNAME, settings.BMC_PASSWORD)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            r = await client.get(url, auth=auth)
            data = r.json()
            temps = data.get("Temperatures", [])
            cpu_temp = None
            for t in temps:
                if "CPU" in t.get("Name", ""):
                    cpu_temp = t.get("ReadingCelsius")
                    break

        psu_url = f"https://{host}/redfish/v1/Chassis/1/Power"
        async with httpx.AsyncClient(verify=False, timeout=10) as client:
            r = await client.get(psu_url, auth=auth)
            pdata = r.json()
            psus = pdata.get("PowerSupplies", [])
            psu_power = psus[0].get("PowerInputWatts") if psus else None
            psu_voltage = psus[0].get("LineInputVoltage") if psus else None

        return {"cpu_temp": cpu_temp, "psu_power": psu_power, "psu_voltage": psu_voltage, "psu_current": None}
    except Exception as e:
        logger.error(f"Redfish 오류 [{host}]: {e}")
        return {}

def collect_via_ipmi(host: str) -> dict:
    try:
        ipm = ipmi_command.Command(
            bmc=host,
            userid=settings.BMC_USERNAME,
            password=settings.BMC_PASSWORD
        )
        sensors = ipm.get_sensor_data()
        cpu_temp = None
        psu_power = None
        for s in sensors:
            name = s.name.upper() if s.name else ""
            if "CPU" in name and "TEMP" in name and cpu_temp is None:
                cpu_temp = s.value
            if "PSU" in name and "POWER" in name and psu_power is None:
                psu_power = s.value
        return {"cpu_temp": cpu_temp, "psu_power": psu_power, "psu_voltage": None, "psu_current": None}
    except Exception as e:
        logger.error(f"IPMI 오류 [{host}]: {e}")
        return {}

async def collect_bmc():
    hosts = [h.strip() for h in settings.BMC_HOSTS.split(",")]
    async with AsyncSessionLocal() as session:
        for host in hosts:
            if settings.BMC_USE_REDFISH:
                data = await collect_via_redfish(host)
            if not data:
                data = await asyncio.to_thread(collect_via_ipmi, host)

            if data:
                record = BMCRecord(
                    host=host,
                    cpu_temp=data.get("cpu_temp"),
                    psu_power=data.get("psu_power"),
                    psu_voltage=data.get("psu_voltage"),
                    psu_current=data.get("psu_current"),
                )
                session.add(record)
        await session.commit()
    logger.info("BMC 수집 완료")
