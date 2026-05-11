"""
이머전 탱크 Modbus 수집기

권장 센서:
  - 온도 (상/하층): CWT-PT100S × 2 (RS485 Modbus RTU, SUS316 침지형 PT100 프로브)
    - 냉각유(오일) 호환, 슬레이브 주소를 각각 다르게 설정
  - 유량: TUF-2000M 초음파 클램프온 유량계 (RS485 Modbus RTU)
    - 비접촉식, 파이프 외부 클램프, 오일 유체 설정 필요

CWT-PT100S 레지스터 맵:
  - 0x0000: 온도 값 × 10 (signed int16) → 253 = 25.3°C
  - 슬레이브 주소: 상층=UPPER_UNIT_ID, 하층=LOWER_UNIT_ID

TUF-2000M 레지스터 맵:
  - 0x0001~0x0002: 순간 유량 float32 (LPM, 메뉴에서 단위 설정)
  - 0x0003~0x0004: 유속 float32 (m/s)
  - 슬레이브 주소: FLOW_UNIT_ID
"""
import struct
from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
from backend.config import settings
from backend.models.database import AsyncSessionLocal, ImmersionTankRecord
import logging

logger = logging.getLogger(__name__)

# Unit ID (슬레이브 주소) - 장비 설정에 맞게 조정
UPPER_TEMP_UNIT_ID = 3   # 상층 CWT-PT100S
LOWER_TEMP_UNIT_ID = 4   # 하층 CWT-PT100S
FLOW_UNIT_ID       = 5   # TUF-2000M

def registers_to_float32(regs) -> float:
    """두 개의 16bit 레지스터를 float32로 변환 (big-endian)"""
    raw = struct.pack(">HH", regs[0], regs[1])
    return struct.unpack(">f", raw)[0]

async def get_modbus_client():
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

async def read_temp(client, unit_id: int) -> float | None:
    """CWT-PT100S: 레지스터 0x0000, 값 × 10 (signed int16)"""
    try:
        rr = await client.read_holding_registers(0x0000, count=1, slave=unit_id)
        if rr.isError():
            return None
        raw = rr.registers[0]
        if raw > 32767:
            raw -= 65536
        return raw / 10.0
    except Exception as e:
        logger.error(f"온도 읽기 오류 (Unit {unit_id}): {e}")
        return None

async def read_flow(client) -> float | None:
    """TUF-2000M: 레지스터 0x0001~0x0002, float32 순간 유량 (LPM)"""
    try:
        rr = await client.read_holding_registers(0x0001, count=2, slave=FLOW_UNIT_ID)
        if rr.isError():
            return None
        return round(registers_to_float32(rr.registers), 2)
    except Exception as e:
        logger.error(f"유량 읽기 오류: {e}")
        return None

async def collect_immersion_tank():
    client = await get_modbus_client()
    try:
        await client.connect()
        temp_upper = await read_temp(client, UPPER_TEMP_UNIT_ID)
        temp_lower = await read_temp(client, LOWER_TEMP_UNIT_ID)
        oil_flow   = await read_flow(client)

        async with AsyncSessionLocal() as session:
            record = ImmersionTankRecord(
                temp_upper=temp_upper,
                temp_lower=temp_lower,
                oil_flow=oil_flow,
            )
            session.add(record)
            await session.commit()

        logger.info(f"이머전 탱크 수집 완료 - 상층: {temp_upper}°C, 하층: {temp_lower}°C, 유량: {oil_flow} LPM")
    except Exception as e:
        logger.error(f"이머전 탱크 수집 오류: {e}")
    finally:
        client.close()
