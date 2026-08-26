from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import Column, Integer, Float, String, DateTime, func

from backend.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class BMCRecord(Base):
    __tablename__ = "bmc_records"
    id = Column(Integer, primary_key=True)
    host = Column(String, nullable=False)
    cpu0_status = Column(String)           # OK / Error / Absent
    cpu1_status = Column(String)
    psu1_status = Column(String)           # OK / Error / Absent
    psu2_status = Column(String)
    power_capacity_watts = Column(Float)   # 최대 전력 용량
    accumulated_energy_joules = Column(Float)  # 누적 에너지
    power_consumed_watts = Column(Float)   # 현재 전력 (0이면 미지원)
    timestamp = Column(DateTime, server_default=func.now())

class HeatExchangerRecord(Base):
    __tablename__ = "heat_exchanger_records"
    id = Column(Integer, primary_key=True)
    pipe_temp = Column(Float)              # CWT-PT100S 클램프온 파이프 온도 (°C)
    water_lpm = Column(Float)             # TUF-2000M 물 유량 (LPM)
    oil_lpm = Column(Float)               # TUF-2000M 냉각유 유량 (LPM, 별도 설치 시)
    timestamp = Column(DateTime, server_default=func.now())

class ImmersionTankRecord(Base):
    __tablename__ = "immersion_tank_records"
    id = Column(Integer, primary_key=True)
    temp_upper = Column(Float)        # 상층 온도 (°C) - CWT-PT100S
    temp_lower = Column(Float)        # 하층 온도 (°C) - CWT-PT100S
    flow_upper = Column(Float)        # 상부 냉각유 유량 (LPM) - 입구, TUF-2000M
    flow_lower = Column(Float)        # 하부 냉각유 유량 (LPM) - 출구, TUF-2000M
    timestamp = Column(DateTime, server_default=func.now())

class PDURecord(Base):
    __tablename__ = "pdu_records"
    id = Column(Integer, primary_key=True)
    unit = Column(String)          # "PDU-1" / "PDU-2" / "PDU-3"
    voltage = Column(Float)        # AC 전압 (V)
    current = Column(Float)        # AC 전류 (A)
    power_factor = Column(Float)   # 역률 (미사용)
    total_power = Column(Float)    # 전력 (W)
    load_rate = Column(Float)      # 부하율 (%) = 전류 / 정격전류(20A) * 100
    temp1 = Column(Float)          # 온도1 (°C, 미사용)
    temp2 = Column(Float)          # 온도2 (°C, 미사용)
    temp3_door = Column(Float)     # 온도3/도어센서 (미사용)
    humidity = Column(Float)       # 습도 (미사용)
    kwh = Column(Float)            # 누적 전력량 (kWh)
    alarm = Column(Integer)        # 알람 상태
    outlet_data = Column(String)   # JSON 문자열 (DEFOG PDU는 아울렛별 계측 미지원 - 미사용)
    timestamp = Column(DateTime, server_default=func.now())

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
