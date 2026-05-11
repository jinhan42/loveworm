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
    cpu_temp = Column(Float)
    psu_power = Column(Float)
    psu_voltage = Column(Float)
    psu_current = Column(Float)
    timestamp = Column(DateTime, server_default=func.now())

class HeatExchangerRecord(Base):
    __tablename__ = "heat_exchanger_records"
    id = Column(Integer, primary_key=True)
    water_lpm = Column(Float)
    oil_lpm = Column(Float)
    timestamp = Column(DateTime, server_default=func.now())

class ImmersionTankRecord(Base):
    __tablename__ = "immersion_tank_records"
    id = Column(Integer, primary_key=True)
    temp_upper = Column(Float)
    temp_lower = Column(Float)
    oil_flow = Column(Float)
    timestamp = Column(DateTime, server_default=func.now())

class PDURecord(Base):
    __tablename__ = "pdu_records"
    id = Column(Integer, primary_key=True)
    total_power = Column(Float)
    outlet_data = Column(String)   # JSON 문자열
    timestamp = Column(DateTime, server_default=func.now())

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
