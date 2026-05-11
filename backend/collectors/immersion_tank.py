"""
이머전 탱크 Modbus 수집기
레지스터 맵 (센서 제조사에 따라 수정 필요):
  - 40001 (0x0000): 상층 온도 (°C x10)
  - 40002 (0x0001): 하층 온도 (°C x10)
  - 40003 (0x0002): 냉각유 흐름 속도 (LPM x10)
"""
from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
from backend.config import settings
from backend.models.database import AsyncSessionLocal, ImmersionTankRecord
import logging

logger = logging.getLogger(__name__)

TEMP_UPPER_REG = 0x0000
TEMP_LOWER_REG = 0x0001
OIL_FLOW_REG   = 0x0002
UNIT_ID        = 1

async def get_modbus_client():
    if settings.IMMERSION_MODE.upper() == "TCP":
        return AsyncModbusTcpClient(
            host=settings.IMMERSION_HOST,
            port=settings.IMMERSION_PORT
        )
    else:
        return AsyncModbusSerialClient(
            port=settings.IMMERSION_SERIAL,
            baudrate=settings.IMMERSION_BAUDRATE,
            parity="N",
            stopbits=1,
            bytesize=8,
        )

async def collect_immersion_tank():
    client = await get_modbus_client()
    try:
        await client.connect()
        rr = await client.read_holding_registers(TEMP_UPPER_REG, count=3, slave=UNIT_ID)
        if rr.isError():
            logger.error(f"이머전 탱크 Modbus 읽기 오류: {rr}")
            return

        temp_upper = rr.registers[0] / 10.0
        temp_lower = rr.registers[1] / 10.0
        oil_flow   = rr.registers[2] / 10.0

        async with AsyncSessionLocal() as session:
            record = ImmersionTankRecord(
                temp_upper=temp_upper,
                temp_lower=temp_lower,
                oil_flow=oil_flow
            )
            session.add(record)
            await session.commit()

        logger.info(f"이머전 탱크 수집 완료 - 상층: {temp_upper}°C, 하층: {temp_lower}°C, 유량: {oil_flow} LPM")
    except Exception as e:
        logger.error(f"이머전 탱크 수집 오류: {e}")
    finally:
        client.close()
