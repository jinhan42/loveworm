from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.config import settings
from backend.collectors.bmc_collector import collect_bmc
from backend.collectors.heat_exchanger import collect_heat_exchanger
from backend.collectors.immersion_tank import collect_immersion_tank
from backend.collectors.pdu_collector import collect_pdu

scheduler = AsyncIOScheduler()

def start_scheduler():
    scheduler.add_job(collect_bmc,            "interval", seconds=settings.COLLECT_INTERVAL_BMC,    id="bmc")
    scheduler.add_job(collect_heat_exchanger, "interval", seconds=settings.COLLECT_INTERVAL_MODBUS,  id="heat_exchanger")
    scheduler.add_job(collect_immersion_tank, "interval", seconds=settings.COLLECT_INTERVAL_MODBUS,  id="immersion_tank")
    scheduler.add_job(collect_pdu,            "interval", seconds=settings.COLLECT_INTERVAL_PDU,     id="pdu")
    scheduler.start()

def stop_scheduler():
    scheduler.shutdown()
