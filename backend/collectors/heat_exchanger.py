"""
열교환기 Modbus 수집기
레지스터 맵 (센서 제조사에 따라 수정 필요):
  - 40001 (0x0000): 물 유량 (LPM x10)
  - 40002 (0x0001): 냉각유 유량 (LPM x10)
"""
import asyncio
from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
from backend.config import settings
from backend.models.database import AsyncSessionLocal, HeatExchangerRecord
import logging

logger = logging.getLogger(__name__)

WATER_FLOW_REG   = 0x0000
OIL_FLOW_REG     = 0x0001
UNIT_ID          = 1

async def get_modbus_client():
    if settings.HEAT_EXCHANGER_MODE.upper() == "TCP":
        return AsyncModbusTcpClient(
            host=settings.HEAT_EXCHANGER_HOST,
            port=settings.HEAT_EXCHANGER_PORT
        )
    else:
        return AsyncModbusSerialClient(
            port=settings.HEAT_EXCHANGER_SERIAL,
            baudrate=settings.HEAT_EXCHANGER_BAUDRATE,
            parity="N",
            stopbits=1,
            bytesize=8,
        )

async def collect_heat_exchanger():
    client = await get_modbus_client()
    try:
        await client.connect()
        rr = await client.read_holding_registers(WATER_FLOW_REG, count=2, slave=UNIT_ID)
        if rr.isError():
            logger.error(f"열교환기 Modbus 읽기 오류: {rr}")
            return

        water_lpm = rr.registers[0] / 10.0
        oil_lpm   = rr.registers[1] / 10.0

        async with AsyncSessionLocal() as session:
            record = HeatExchangerRecord(water_lpm=water_lpm, oil_lpm=oil_lpm)
            session.add(record)
            await session.commit()

        logger.info(f"열교환기 수집 완료 - 물: {water_lpm} LPM, 냉각유: {oil_lpm} LPM")
    except Exception as e:
        logger.error(f"열교환기 수집 오류: {e}")
    finally:
        client.close()
