"""
이머전 탱크 Modbus 수집기

센서 구성:
  - 상층 온도: CWT-PT100S (슬레이브 3) + SUS316 침지 프로브 300mm
  - 하층 온도: CWT-PT100S (슬레이브 4) + SUS316 침지 프로브 600mm
  - 상부 유량: TUF-2000M (슬레이브 5) - 냉각유 입구 파이프 클램프온
  - 하부 유량: TUF-2000M (슬레이브 6) - 냉각유 출구 파이프 클램프온 (빨간 볼밸브 연결)

냉각유 순환 흐름:
  차가운 냉각유 → [상부 입구 파이프] → 탱크 상층
  뜨거운 냉각유 → [하부 출구 파이프] → 열교환기

TUF-2000M Modbus 레지스터 (Function Code 03):
  0x0001~0x0002: 순간 유량 float32 (LPM - 메뉴에서 단위 설정)

CWT-PT100S Modbus 레지스터 (Function Code 03):
  0x0000: 온도 × 10 (signed int16)
"""
import struct
from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
from backend.config import settings
from backend.models.database import AsyncSessionLocal, ImmersionTankRecord
import logging

logger = logging.getLogger(__name__)

# 슬레이브 주소 (장비 설정과 일치시켜야 함)
UPPER_TEMP_UNIT_ID  = 3   # CWT-PT100S 상층 온도
LOWER_TEMP_UNIT_ID  = 4   # CWT-PT100S 하층 온도
UPPER_FLOW_UNIT_ID  = 5   # TUF-2000M 상부 입구 유량
LOWER_FLOW_UNIT_ID  = 6   # TUF-2000M 하부 출구 유량

def to_float32(regs) -> float:
    raw = struct.pack(">HH", regs[0], regs[1])
    return struct.unpack(">f", raw)[0]

async def get_client():
    if settings.IMMERSION_MODE.upper() == "TCP":
        return AsyncModbusTcpClient(
            host=settings.IMMERSION_HOST,
            port=settings.IMMERSION_PORT
        )
    return AsyncModbusSerialClient(
        port=settings.IMMERSION_SERIAL,
        baudrate=settings.IMMERSION_BAUDRATE,
        parity="N", stopbits=1, bytesize=8,
    )

async def read_temp(client, unit_id: int, label: str) -> float | None:
    """CWT-PT100S: 레지스터 0x0000, signed int16 × 0.1"""
    try:
        rr = await client.read_holding_registers(0x0000, count=1, slave=unit_id)
        if rr.isError():
            return None
        raw = rr.registers[0]
        if raw > 32767:
            raw -= 65536
        return raw / 10.0
    except Exception as e:
        logger.error(f"온도 읽기 오류 [{label}]: {e}")
        return None

async def read_flow(client, unit_id: int, label: str) -> float | None:
    """TUF-2000M: 레지스터 0x0001~0x0002, float32 순간 유량 (LPM)"""
    try:
        rr = await client.read_holding_registers(0x0001, count=2, slave=unit_id)
        if rr.isError():
            return None
        val = to_float32(rr.registers)
        return round(val, 2)
    except Exception as e:
        logger.error(f"유량 읽기 오류 [{label}]: {e}")
        return None

async def collect_immersion_tank():
    client = await get_client()
    try:
        await client.connect()

        temp_upper  = await read_temp(client,  UPPER_TEMP_UNIT_ID,  "상층온도")
        temp_lower  = await read_temp(client,  LOWER_TEMP_UNIT_ID,  "하층온도")
        flow_upper  = await read_flow(client,  UPPER_FLOW_UNIT_ID,  "상부유량")
        flow_lower  = await read_flow(client,  LOWER_FLOW_UNIT_ID,  "하부유량")

        async with AsyncSessionLocal() as session:
            record = ImmersionTankRecord(
                temp_upper=temp_upper,
                temp_lower=temp_lower,
                flow_upper=flow_upper,
                flow_lower=flow_lower,
            )
            session.add(record)
            await session.commit()

        logger.info(
            f"이머전 탱크 수집 완료 | "
            f"상층: {temp_upper}°C / 하층: {temp_lower}°C | "
            f"입구유량: {flow_upper} LPM / 출구유량: {flow_lower} LPM"
        )
    except Exception as e:
        logger.error(f"이머전 탱크 수집 오류: {e}")
    finally:
        client.close()
