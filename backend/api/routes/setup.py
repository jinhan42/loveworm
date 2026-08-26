import re
import threading
import time
import subprocess
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["setup"])

ENV_FILE = Path(__file__).parent.parent.parent / ".env"

SETUP_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UniTank 초기 설정</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  input, select { background-color: #374151; color: white; }
  input::placeholder { color: #9CA3AF; }
</style>
</head>
<body class="bg-gray-900 text-white min-h-screen">
<div class="max-w-2xl mx-auto p-6">
  <div class="text-center mb-8">
    <div class="text-green-400 text-3xl font-bold mb-2">⚙ UniTank 초기 설정</div>
    <p class="text-gray-400">이 페이지는 최초 1회만 표시됩니다. 장비 정보를 입력하세요.</p>
  </div>

  <form id="setupForm" class="space-y-6">

    <!-- 유닛 이름 -->
    <div class="bg-gray-800 rounded-lg p-5">
      <h2 class="text-green-400 font-semibold text-lg mb-4">📋 유닛 정보</h2>
      <div>
        <label class="block text-sm text-gray-400 mb-1">유닛 이름 (탱크 식별자)</label>
        <input type="text" name="unit_name" placeholder="예: Tank-01, SKT-TESTBED-01"
          class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
      </div>
    </div>

    <!-- BMC 설정 -->
    <div class="bg-gray-800 rounded-lg p-5">
      <h2 class="text-green-400 font-semibold text-lg mb-4">🖥 BMC 서버 설정</h2>
      <div class="space-y-3">
        <div>
          <label class="block text-sm text-gray-400 mb-1">BMC IP 주소 (쉼표로 여러 대 입력)</label>
          <input type="text" name="bmc_hosts" placeholder="192.168.1.100,192.168.1.101"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm text-gray-400 mb-1">BMC 사용자명</label>
            <input type="text" name="bmc_username" placeholder="admin"
              class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">BMC 비밀번호</label>
            <input type="password" name="bmc_password" placeholder="password"
              class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
          </div>
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-1">프로토콜</label>
          <select name="bmc_use_redfish"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
            <option value="true">Redfish API (권장)</option>
            <option value="false">IPMI</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 열교환기 설정 -->
    <div class="bg-gray-800 rounded-lg p-5">
      <h2 class="text-green-400 font-semibold text-lg mb-4">🌡 열교환기 설정</h2>
      <div class="space-y-3">
        <div>
          <label class="block text-sm text-gray-400 mb-1">통신 방식</label>
          <select name="heat_exchanger_mode" id="hxMode"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none"
            onchange="toggleMode('hx', this.value)">
            <option value="TCP">Modbus TCP</option>
            <option value="RTU">Modbus RTU (시리얼)</option>
          </select>
        </div>
        <div id="hxTcp">
          <label class="block text-sm text-gray-400 mb-1">열교환기 IP</label>
          <input type="text" name="heat_exchanger_host" placeholder="192.168.1.200"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
        </div>
        <div id="hxRtu" class="hidden">
          <label class="block text-sm text-gray-400 mb-1">시리얼 포트</label>
          <input type="text" name="heat_exchanger_serial" placeholder="/dev/ttyUSB0"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-1">Modbus 포트</label>
          <input type="number" name="heat_exchanger_port" value="502"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
        </div>
      </div>
    </div>

    <!-- 이머전 탱크 설정 -->
    <div class="bg-gray-800 rounded-lg p-5">
      <h2 class="text-green-400 font-semibold text-lg mb-4">🛢 이머전 탱크 설정</h2>
      <div class="space-y-3">
        <div>
          <label class="block text-sm text-gray-400 mb-1">통신 방식</label>
          <select name="immersion_mode" id="immMode"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none"
            onchange="toggleMode('imm', this.value)">
            <option value="TCP">Modbus TCP</option>
            <option value="RTU">Modbus RTU (시리얼)</option>
          </select>
        </div>
        <div id="immTcp">
          <label class="block text-sm text-gray-400 mb-1">이머전 탱크 IP</label>
          <input type="text" name="immersion_host" placeholder="192.168.1.201"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
        </div>
        <div id="immRtu" class="hidden">
          <label class="block text-sm text-gray-400 mb-1">시리얼 포트</label>
          <input type="text" name="immersion_serial" placeholder="/dev/ttyUSB1"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-1">Modbus 포트</label>
          <input type="number" name="immersion_port" value="502"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
        </div>
      </div>
    </div>

    <!-- PDU 설정 -->
    <div class="bg-gray-800 rounded-lg p-5">
      <h2 class="text-green-400 font-semibold text-lg mb-4">🔌 PDU 설정</h2>
      <div class="space-y-3">
        <div>
          <label class="block text-sm text-gray-400 mb-1">PDU IP 주소 (쉼표로 구분, 순서대로 PDU-1, PDU-2, ...)</label>
          <input type="text" name="pdu_hosts" placeholder="10.230.200.1,10.230.200.2,10.230.200.3"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-sm text-gray-400 mb-1">서버용 PDU 대수 (앞에서부터, 나머지는 TANK+CDU)</label>
            <input type="number" name="pdu_server_count" value="2"
              class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">SNMP Community</label>
            <input type="text" name="pdu_snmp_community" placeholder="public"
              class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
          </div>
        </div>
      </div>
    </div>

    <!-- 수집 주기 -->
    <div class="bg-gray-800 rounded-lg p-5">
      <h2 class="text-green-400 font-semibold text-lg mb-4">⏱ 데이터 수집 주기</h2>
      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="block text-sm text-gray-400 mb-1">BMC (초)</label>
          <input type="number" name="collect_interval_bmc" value="30"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-1">Modbus (초)</label>
          <input type="number" name="collect_interval_modbus" value="10"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-1">PDU (초)</label>
          <input type="number" name="collect_interval_pdu" value="30"
            class="w-full px-3 py-2 rounded border border-gray-600 focus:border-green-400 outline-none">
        </div>
      </div>
    </div>

    <!-- 저장 버튼 -->
    <button type="submit" id="submitBtn"
      class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-4 rounded-lg text-lg transition">
      설정 저장 및 시작
    </button>

    <div id="statusMsg" class="hidden text-center py-4 rounded-lg bg-gray-800"></div>
  </form>
</div>

<script>
function toggleMode(prefix, value) {
  const tcpDiv = document.getElementById(prefix + 'Tcp');
  const rtuDiv = document.getElementById(prefix + 'Rtu');
  if (value === 'TCP') {
    tcpDiv.classList.remove('hidden');
    rtuDiv.classList.add('hidden');
  } else {
    tcpDiv.classList.add('hidden');
    rtuDiv.classList.remove('hidden');
  }
}

document.getElementById('setupForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('submitBtn');
  const msg = document.getElementById('statusMsg');
  btn.disabled = true;
  btn.textContent = '저장 중...';

  const formData = new FormData(e.target);
  const data = {};
  formData.forEach((val, key) => { if (val) data[key] = val; });

  try {
    const res = await fetch('/api/setup', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    if (res.ok) {
      msg.className = 'text-center py-4 rounded-lg bg-green-900 text-green-300';
      msg.textContent = '✅ 설정이 저장되었습니다. 서비스가 재시작됩니다. 잠시 후 대시보드로 이동합니다...';
      msg.classList.remove('hidden');
      btn.textContent = '재시작 중...';
      setTimeout(() => {
        const poll = setInterval(async () => {
          try {
            const r = await fetch('/api/health');
            if (r.ok) { clearInterval(poll); window.location.href = '/'; }
          } catch {}
        }, 2000);
      }, 3000);
    } else {
      throw new Error(await res.text());
    }
  } catch (err) {
    msg.className = 'text-center py-4 rounded-lg bg-red-900 text-red-300';
    msg.textContent = '❌ 오류: ' + err.message;
    msg.classList.remove('hidden');
    btn.disabled = false;
    btn.textContent = '설정 저장 및 시작';
  }
});
</script>
</body>
</html>"""


class SetupData(BaseModel):
    unit_name: Optional[str] = None
    bmc_hosts: Optional[str] = None
    bmc_username: Optional[str] = None
    bmc_password: Optional[str] = None
    bmc_use_redfish: Optional[str] = None
    heat_exchanger_mode: Optional[str] = None
    heat_exchanger_host: Optional[str] = None
    heat_exchanger_port: Optional[str] = None
    heat_exchanger_serial: Optional[str] = None
    heat_exchanger_baudrate: Optional[str] = None
    immersion_mode: Optional[str] = None
    immersion_host: Optional[str] = None
    immersion_port: Optional[str] = None
    immersion_serial: Optional[str] = None
    immersion_baudrate: Optional[str] = None
    pdu_hosts: Optional[str] = None
    pdu_server_count: Optional[str] = None
    pdu_snmp_community: Optional[str] = None
    collect_interval_bmc: Optional[str] = None
    collect_interval_modbus: Optional[str] = None
    collect_interval_pdu: Optional[str] = None


@router.get("/setup", response_class=HTMLResponse)
async def setup_page():
    return HTMLResponse(content=SETUP_HTML)


@router.get("/api/setup/status")
async def setup_status():
    from backend.config import settings
    return {"configured": settings.CONFIGURED, "unit_name": settings.UNIT_NAME}


@router.post("/api/setup")
async def save_setup(data: SetupData):
    field_map = {
        "unit_name":               "UNIT_NAME",
        "bmc_hosts":               "BMC_HOSTS",
        "bmc_username":            "BMC_USERNAME",
        "bmc_password":            "BMC_PASSWORD",
        "bmc_use_redfish":         "BMC_USE_REDFISH",
        "heat_exchanger_mode":     "HEAT_EXCHANGER_MODE",
        "heat_exchanger_host":     "HEAT_EXCHANGER_HOST",
        "heat_exchanger_port":     "HEAT_EXCHANGER_PORT",
        "heat_exchanger_serial":   "HEAT_EXCHANGER_SERIAL",
        "heat_exchanger_baudrate": "HEAT_EXCHANGER_BAUDRATE",
        "immersion_mode":          "IMMERSION_MODE",
        "immersion_host":          "IMMERSION_HOST",
        "immersion_port":          "IMMERSION_PORT",
        "immersion_serial":        "IMMERSION_SERIAL",
        "immersion_baudrate":      "IMMERSION_BAUDRATE",
        "pdu_hosts":               "PDU_HOSTS",
        "pdu_server_count":        "PDU_SERVER_COUNT",
        "pdu_snmp_community":      "PDU_SNMP_COMMUNITY",
        "collect_interval_bmc":    "COLLECT_INTERVAL_BMC",
        "collect_interval_modbus": "COLLECT_INTERVAL_MODBUS",
        "collect_interval_pdu":    "COLLECT_INTERVAL_PDU",
    }

    lines = []
    data_dict = data.model_dump()
    for key, env_key in field_map.items():
        val = data_dict.get(key)
        if val is not None and val != "":
            lines.append(f"{env_key}={val}")

    lines.append("CONFIGURED=true")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 호스트명을 unit_name 기반으로 변경 (소문자, 영숫자-하이픈만 허용)
    unit_name = data.unit_name or "unitank"
    hostname = re.sub(r'[^a-z0-9-]', '-', unit_name.lower()).strip('-') or "unitank"
    hostname = re.sub(r'-+', '-', hostname)[:63]

    def delayed_restart():
        time.sleep(2)
        subprocess.run(["sudo", "hostnamectl", "set-hostname", hostname], check=False)
        subprocess.run(["sudo", "systemctl", "restart", "loveworm"], check=False)

    threading.Thread(target=delayed_restart, daemon=True).start()
    return JSONResponse({"ok": True, "hostname": hostname})
