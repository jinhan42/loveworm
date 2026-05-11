"""
PDU 수집기 - SNMP 및 Modbus 지원
"""
import json
import asyncio
from pysnmp.hlapi.asyncio import (
    getCmd, SnmpEngine, CommunityData, UdpTransportTarget,
    ContextData, ObjectType, ObjectIdentity
)
from pymodbus.client import AsyncModbusTcpClient
from backend.config import settings
from backend.models.database import AsyncSessionLocal, PDURecord
import logging

logger = logging.getLogger(__name__)

# SNMP OID (APC/Raritan 등 표준 PDU OID - 제품에 따라 수정)
OID_TOTAL_POWER  = "1.3.6.1.4.1.318.1.1.12.1.16.0"   # APC 예시
OID_OUTLET_POWER = "1.3.6.1.4.1.318.1.1.12.3.5.1.1.2" # APC 아울렛별 예시

async def collect_via_snmp() -> dict:
    engine = SnmpEngine()
    results = {}
    try:
        error_indication, error_status, _, var_binds = await getCmd(
            engine,
            CommunityData(settings.PDU_SNMP_COMMUNITY),
            await UdpTransportTarget.create((settings.PDU_HOST, settings.PDU_SNMP_PORT)),
            ContextData(),
            ObjectType(ObjectIdentity(OID_TOTAL_POWER)),
        )
        if not error_indication and not error_status:
            results["total_power"] = float(var_binds[0][1])
    except Exception as e:
        logger.error(f"PDU SNMP 오류: {e}")
    return results

async def collect_via_modbus() -> dict:
    client = AsyncModbusTcpClient(host=settings.PDU_HOST, port=settings.PDU_MODBUS_PORT)
    results = {}
    try:
        await client.connect()
        rr = await client.read_holding_registers(0x0000, count=8, slave=1)
        if not rr.isError():
            results["total_power"] = rr.registers[0] / 10.0
            outlets = {f"outlet_{i+1}": rr.registers[i] / 10.0 for i in range(1, 8)}
            results["outlets"] = outlets
    except Exception as e:
        logger.error(f"PDU Modbus 오류: {e}")
    finally:
        client.close()
    return results

async def collect_pdu():
    data = await collect_via_snmp()
    if not data:
        data = await collect_via_modbus()

    if data:
        async with AsyncSessionLocal() as session:
            record = PDURecord(
                total_power=data.get("total_power"),
                outlet_data=json.dumps(data.get("outlets", {}))
            )
            session.add(record)
            await session.commit()
        logger.info(f"PDU 수집 완료 - 전체 전력: {data.get('total_power')} W")
