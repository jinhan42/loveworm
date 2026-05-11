from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./loveworm.db"

    # BMC 서버 목록 (쉼표 구분)
    BMC_HOSTS: str = "192.168.1.100,192.168.1.101"
    BMC_USERNAME: str = "admin"
    BMC_PASSWORD: str = "admin"
    BMC_USE_REDFISH: bool = True

    # Modbus 열교환기
    HEAT_EXCHANGER_MODE: str = "TCP"       # RTU or TCP
    HEAT_EXCHANGER_HOST: Optional[str] = "192.168.1.200"  # TCP용
    HEAT_EXCHANGER_PORT: int = 502
    HEAT_EXCHANGER_SERIAL: Optional[str] = "/dev/ttyUSB0"  # RTU용
    HEAT_EXCHANGER_BAUDRATE: int = 9600

    # Modbus 이머전 탱크
    IMMERSION_MODE: str = "TCP"
    IMMERSION_HOST: Optional[str] = "192.168.1.201"
    IMMERSION_PORT: int = 502
    IMMERSION_SERIAL: Optional[str] = "/dev/ttyUSB1"
    IMMERSION_BAUDRATE: int = 9600

    # PDU
    PDU_HOST: str = "192.168.1.210"
    PDU_SNMP_COMMUNITY: str = "public"
    PDU_SNMP_PORT: int = 161
    PDU_MODBUS_PORT: int = 502

    # 수집 주기 (초)
    COLLECT_INTERVAL_BMC: int = 30
    COLLECT_INTERVAL_MODBUS: int = 10
    COLLECT_INTERVAL_PDU: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
