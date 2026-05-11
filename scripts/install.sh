#!/bin/bash
# Raspberry Pi 5 자동 설치 스크립트

set -e
echo "=== Loveworm 모니터링 시스템 설치 시작 ==="

# 시스템 패키지 업데이트
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-venv nodejs npm git

# Node.js 최신 버전 설치
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 프로젝트 클론 (이미 있으면 스킵)
if [ ! -d "/home/pi/loveworm" ]; then
  git clone https://github.com/jinhan42/loveworm.git /home/pi/loveworm
fi

cd /home/pi/loveworm

# Backend Python 가상환경 설정
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt

# Frontend 빌드
cd frontend
npm install
npm run build
cd ..

# .env 파일 생성 (초기값)
if [ ! -f "backend/.env" ]; then
  cat > backend/.env << 'ENV'
BMC_HOSTS=192.168.1.100
BMC_USERNAME=admin
BMC_PASSWORD=admin
BMC_USE_REDFISH=true
HEAT_EXCHANGER_MODE=TCP
HEAT_EXCHANGER_HOST=192.168.1.200
IMMERSION_MODE=TCP
IMMERSION_HOST=192.168.1.201
PDU_HOST=192.168.1.210
PDU_SNMP_COMMUNITY=public
ENV
  echo ".env 파일 생성됨 - 실제 IP/비밀번호로 수정하세요!"
fi

# systemd 서비스 등록
sudo cp scripts/loveworm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable loveworm
sudo systemctl start loveworm

echo "=== 설치 완료! http://라즈베리파이IP:8000 으로 접속하세요 ==="
