"""
열교환기 Modbus 수집기

권장 센서:
  - 온도: CWT-PT100S (RS485 Modbus RTU, PT100 클램프온 프로브)
  - 유량: TUF-2000M 초음파 클램프온 유량계 (RS485 Modbus RTU)

CWT-PT100S 레지스터 맵 (Unit ID: HEAT_EXCHANGER_TEMP_UNIT_ID):
  - 0x0000: 온도 값 × 10 (signed int16) → 253 = 25.3°C

TUF-2000M 레지스터 맵 (Unit ID: HEAT_EXCHANGER_FLOW_UNIT_ID):
  - 0x0001: 순간 유량 float32 (상위 16bit) - 2개 레지스터
  - 0x0002: 순간 유량 float32 (하위 16bit)
  단위는 TUF-2000M 메뉴에서 L/min(LPM)으로 설정 필요
"""
import struct
import asyncio
from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
from backend.config import settings
from backend.models.database import AsyncSessionLocal, HeatExchangerRecord
import logging

logger = logging.getLogger(__name__)

# Unit ID 설정 (장비별 슬레이브 주소)
TEMP_UNIT_ID = 1    # CWT-PT100S 슬레이브 주소
FLOW_UNIT_ID = 2    # TUF-2000M 슬레이브 주소

def registers_to_float32(regs) -> float:
    """두 개의 16bit 레지스터를 float32로 변환 (big-endian)"""
    raw = struct.pack(">HH", regs[0], regs[1])
    return struct.unpack(">f", raw)[0]

async def get_modbus_client():
    if settings.HEAT_EXCHANGER_MODE.upper() == "TCP":
        return AsyncModbusTcpClient(
            host=settings.HEAT_EXCHANGER_HOST,
            port=settings.HEAT_EXCHANGER_PORT
        )
    return AsyncModbusSerialClient(
        port=settings.HEAT_EXCHANGER_SERIAL,
        baudrate=settings.HEAT_EXCHANGER_BAUDRATE,
        parity="N", stopbits=1, bytesize=8,
    )

async def read_temperature(client) -> float | None:
    """CWT-PT100S: 레지스터 0x0000, 값 × 10"""
    try:
        rr = await client.read_holding_registers(0x0000, count=1, slave=TEMP_UNIT_ID)
        if rr.isError():
            return None
        raw = rr.registers[0]
        # signed int16 처리
        if raw > 32767:
            raw -= 65536
        return raw / 10.0
    except Exception as e:
        logger.error(f"열교환기 온도 읽기 오류: {e}")
        return None

async def read_water_flow(client) -> float | None:
    """TUF-2000M: 레지스터 0x0001~0x0002, float32 순간 유량"""
    try:
        rr = await client.read_holding_registers(0x0001, count=2, slave=FLOW_UNIT_ID)
        if rr.isError():
            return None
        return round(registers_to_float32(rr.registers), 2)
    except Exception as e:
        logger.error(f"열교환기 유량 읽기 오류: {e}")
        return None

async def collect_heat_exchanger():
    client = await get_modbus_client()
    try:
        await client.connect()
        pipe_temp  = await read_temperature(client)
        water_flow = await read_water_flow(client)

        async with AsyncSessionLocal() as session:
            record = HeatExchangerRecord(
                water_lpm=water_flow,
                oil_lpm=None,          # 냉각유 유량계 별도 설치 시 추가
                pipe_temp=pipe_temp,
            )
            session.add(record)
            await session.commit()

        logger.info(f"열교환기 수집 완료 - 파이프 온도: {pipe_temp}°C, 물 유량: {water_flow} LPM")
    except Exception as e:
        logger.error(f"열교환기 수집 오류: {e}")
    finally:
        client.close()
