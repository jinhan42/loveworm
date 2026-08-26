from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

ENV_FILE = Path(__file__).parent / ".env"

class Settings(BaseSettings):
    # 유닛 설정
    UNIT_NAME: str = "UniTank"
    CONFIGURED: bool = False

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./loveworm.db"

    # BMC 서버 목록 (쉼표 구분)
    BMC_HOSTS: str = "192.168.1.100"
    BMC_USERNAME: str = "admin"
    BMC_PASSWORD: str = "admin"
    BMC_USE_REDFISH: bool = True

    # Modbus 열교환기
    HEAT_EXCHANGER_MODE: str = "TCP"
    HEAT_EXCHANGER_HOST: Optional[str] = "192.168.1.200"
    HEAT_EXCHANGER_PORT: int = 502
    HEAT_EXCHANGER_SERIAL: Optional[str] = "/dev/ttyUSB0"
    HEAT_EXCHANGER_BAUDRATE: int = 9600

    # Modbus 이머전 탱크
    IMMERSION_MODE: str = "TCP"
    IMMERSION_HOST: Optional[str] = "192.168.1.201"
    IMMERSION_PORT: int = 502
    IMMERSION_SERIAL: Optional[str] = "/dev/ttyUSB1"
    IMMERSION_BAUDRATE: int = 9600

    # PDU (DEFOG KC10-20ELPM, SNMP) - 쉼표 구분, 순서대로 PDU-1, PDU-2, PDU-3 ...
    PDU_HOSTS: str = "10.230.200.1,10.230.200.2,10.230.200.3"
    PDU_SERVER_COUNT: int = 2  # 앞에서부터 N대가 서버 전원, 나머지는 TANK+CDU
    PDU_SNMP_COMMUNITY: str = "public"

    # 수집 주기 (초)
    COLLECT_INTERVAL_BMC: int = 30
    COLLECT_INTERVAL_MODBUS: int = 10
    COLLECT_INTERVAL_PDU: int = 30

    class Config:
        env_file = str(ENV_FILE)

settings = Settings()
