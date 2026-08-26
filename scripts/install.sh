#!/bin/bash
# UniTank 모니터링 시스템 설치 스크립트
# Raspberry Pi OS (Debian 기반) 전용

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CURRENT_USER="${SUDO_USER:-$(whoami)}"
USER_HOME="$(eval echo ~$CURRENT_USER)"

echo "======================================================"
echo "  UniTank 모니터링 시스템 설치"
echo "======================================================"
echo "  프로젝트 경로: $PROJECT_DIR"
echo "  실행 사용자:   $CURRENT_USER"
echo "======================================================"

# 시스템 패키지 설치
echo ""
echo "[1/5] 시스템 패키지 설치..."
sudo apt-get update -q
sudo apt-get install -y python3-pip python3-venv git curl

# Node.js 20 설치 (프론트엔드 빌드용)
if ! command -v node &>/dev/null || [[ "$(node -v)" < "v20" ]]; then
  echo "      Node.js 20 설치 중..."
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi
echo "      완료 (Node: $(node -v), Python: $(python3 --version))"

# Python 가상환경 및 패키지 설치
echo ""
echo "[2/5] Python 패키지 설치..."
python3 -m venv "$PROJECT_DIR/backend/venv"
"$PROJECT_DIR/backend/venv/bin/pip" install -q --upgrade pip
"$PROJECT_DIR/backend/venv/bin/pip" install -q -r "$PROJECT_DIR/backend/requirements.txt"
echo "      완료"

# 프론트엔드 빌드
echo ""
echo "[3/5] 프론트엔드 빌드..."
cd "$PROJECT_DIR/frontend"
npm install --silent
npm run build --silent
echo "      완료"

# .env 파일 생성 (없을 경우만)
echo ""
echo "[4/5] 환경 설정..."
if [ ! -f "$PROJECT_DIR/backend/.env" ]; then
  cat > "$PROJECT_DIR/backend/.env" << 'ENVEOF'
UNIT_NAME=UniTank
CONFIGURED=false
BMC_HOSTS=192.168.1.100
BMC_USERNAME=admin
BMC_PASSWORD=admin
BMC_USE_REDFISH=true
HEAT_EXCHANGER_MODE=TCP
HEAT_EXCHANGER_HOST=192.168.1.200
HEAT_EXCHANGER_PORT=502
IMMERSION_MODE=TCP
IMMERSION_HOST=192.168.1.201
IMMERSION_PORT=502
PDU_HOST=192.168.1.210
PDU_SNMP_COMMUNITY=public
PDU_SNMP_PORT=161
PDU_MODBUS_PORT=502
COLLECT_INTERVAL_BMC=30
COLLECT_INTERVAL_MODBUS=10
COLLECT_INTERVAL_PDU=30
ENVEOF
  echo "      .env 파일 생성됨 (첫 부팅 시 웹 UI에서 설정)"
else
  echo "      .env 파일 이미 존재 (유지)"
fi

# sudoers 설정 (서비스 재시작 권한)
SUDOERS_FILE="/etc/sudoers.d/loveworm"
if [ ! -f "$SUDOERS_FILE" ]; then
  echo "$CURRENT_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart loveworm" | sudo tee "$SUDOERS_FILE" > /dev/null
  sudo chmod 440 "$SUDOERS_FILE"
  echo "      sudoers 설정 완료"
fi

# systemd 서비스 등록
echo ""
echo "[5/5] systemd 서비스 등록..."
sudo tee /etc/systemd/system/loveworm.service > /dev/null << SVCEOF
[Unit]
Description=UniTank Monitoring System
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/backend/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONPATH=$PROJECT_DIR
EnvironmentFile=$PROJECT_DIR/backend/.env

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable loveworm
sudo systemctl restart loveworm

echo ""
echo "======================================================"
echo "  설치 완료!"
echo "======================================================"
echo ""
echo "  웹 UI: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "  첫 접속 시 초기 설정 페이지가 표시됩니다."
echo "  장비 IP 및 인증 정보를 입력하세요."
echo ""
