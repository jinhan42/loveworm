"""
DEFOG PDU (KC10-20ELPM) SNMP 폴링 모듈
MIB: POWER METER SNMP_DEFOG.mib (enterprises.pwrmeter = 1.3.6.1.4.1.6375)

다른 프로그램에서 재사용할 수 있도록 UI/서버 코드와 분리됨.
필요 패키지: pysnmp (pip install pysnmp)
"""
import asyncio
from pysnmp.hlapi.asyncio import (
    SnmpEngine, CommunityData, UdpTransportTarget,
    ContextData, ObjectType, ObjectIdentity,
)
try:
    from pysnmp.hlapi.asyncio import get_cmd  # pysnmp 7.x
except ImportError:
    from pysnmp.hlapi.asyncio import getCmd as get_cmd  # pysnmp 6.x

DEFAULT_COMMUNITY = "public"
RATED_CURRENT_A = 20  # 모델명 KC10-20ELPM 기준 정격전류 (부하율 계산용)

# pysnmp 6.x는 UdpTransportTarget(...)를 동기 생성자로 쓰고,
# pysnmp 7.x는 await UdpTransportTarget.create(...) 비동기 팩토리로 바뀜.
# 같은 Pi라도 venv마다 설치된 버전이 다를 수 있어 둘 다 지원하도록 분기.
async def _make_target(ip: str, timeout: int, retries: int):
    if hasattr(UdpTransportTarget, "create"):
        return await UdpTransportTarget.create((ip, 161), timeout=timeout, retries=retries)
    return UdpTransportTarget((ip, 161), timeout=timeout, retries=retries)

BASE_OID = "1.3.6.1.4.1.6375.1"
FIELDS = {
    "voltage": (BASE_OID + ".1.0", "전압", "V"),
    "current": (BASE_OID + ".2.0", "전류", "A"),
    "power":   (BASE_OID + ".4.0", "전력", "W"),
    "kwh":     (BASE_OID + ".9.0", "누적 전력량", "kWh"),
    "alarm":   (BASE_OID + ".10.0", "알람", ""),
}


async def poll_pdu(ip: str, community: str = DEFAULT_COMMUNITY, timeout: int = 2, retries: int = 1) -> dict:
    """PDU 1대 조회. 실패 시 예외 발생.
    반환: {"voltage":.., "current":.., "power":.., "kwh":.., "alarm":.., "load_rate":..}
    - load_rate: 전류 기준 부하율(%) = current / RATED_CURRENT_A * 100 (SNMP 값이 아닌 계산값)
    """
    engine = SnmpEngine()
    target = await _make_target(ip, timeout, retries)
    values = {}
    for field, (oid, _, _) in FIELDS.items():
        error_indication, error_status, _, var_binds = await get_cmd(
            engine,
            CommunityData(community, mpModel=1),
            target,
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        )
        if error_indication or error_status:
            raise RuntimeError(str(error_indication or error_status.prettyPrint()))
        values[field] = float(var_binds[0][1])
    values["load_rate"] = values["current"] / RATED_CURRENT_A * 100
    return values


def poll_pdu_sync(ip: str, **kwargs) -> dict:
    """동기 코드에서 호출할 때 사용 (asyncio.run 래퍼)."""
    return asyncio.run(poll_pdu(ip, **kwargs))


async def poll_many(pdus: dict, **kwargs) -> dict:
    """{name: ip} 형태로 여러 대를 순차 조회.
    반환: {name: {"values": {...} 또는 {}, "error": None 또는 str}}"""
    results = {}
    for name, ip in pdus.items():
        try:
            results[name] = {"values": await poll_pdu(ip, **kwargs), "error": None}
        except Exception as e:
            results[name] = {"values": {}, "error": str(e)}
    return results


def summarize(results: dict) -> dict:
    """poll_many() 결과를 합산. 반환: {"current":.., "power":.., "kwh":.., "online":N, "total":N}"""
    total = {"current": 0.0, "power": 0.0, "kwh": 0.0}
    online = 0
    for entry in results.values():
        if entry["values"]:
            online += 1
            for k in total:
                total[k] += entry["values"].get(k, 0.0)
    total["online"] = online
    total["total"] = len(results)
    return total
