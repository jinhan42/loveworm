#!/bin/bash
# 배포 이미지 준비 스크립트
# SD카드 복제 전 이 스크립트를 실행하여 개인 정보 및 설정을 초기화합니다.

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_USER="$(stat -c '%U' "$PROJECT_DIR")"

echo "======================================================"
echo "  UniTank 배포 이미지 준비 스크립트"
echo "======================================================"
echo ""
echo "이 스크립트는 다음 작업을 수행합니다:"
echo "  1. loveworm 서비스 중지"
echo "  2. DB 초기화 (데이터 삭제)"
echo "  3. .env 파일 기본값으로 초기화"
echo "  4. 로그 파일 삭제"
echo "  5. SSH 호스트 키 재생성 설정"
echo "  6. bash 히스토리 삭제"
echo ""

read -p "계속하시겠습니까? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
  echo "취소되었습니다."
  exit 0
fi

echo ""
echo "[1/6] loveworm 서비스 중지..."
sudo systemctl stop loveworm || true

echo "[2/6] DB 초기화..."
if [ -f "$PROJECT_DIR/loveworm.db" ]; then
  rm -f "$PROJECT_DIR/loveworm.db"
  echo "      loveworm.db 삭제 완료"
fi

echo "[3/6] .env 파일 초기화..."
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
echo "      .env 초기화 완료"

echo "[4/6] 로그 파일 삭제..."
sudo journalctl --rotate --vacuum-time=1s 2>/dev/null || true
sudo find /var/log -name "*.log" -delete 2>/dev/null || true
sudo find /var/log -name "*.gz" -delete 2>/dev/null || true
echo "      로그 삭제 완료"

echo "[5/6] 호스트명 초기화 및 SSH 호스트 키 재생성 설정..."
echo 'Uniwide1!' | sudo -S hostnamectl set-hostname unitank 2>/dev/null || sudo hostnamectl set-hostname unitank
echo "      호스트명 -> unitank (unitank.local 으로 접속 가능)"

echo "      SSH 호스트 키 재생성 설정..."
sudo rm -f /etc/ssh/ssh_host_*
sudo tee /etc/rc.local > /dev/null << 'RCEOF'
#!/bin/bash
# 첫 부팅 시 SSH 호스트 키 재생성
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
  dpkg-reconfigure openssh-server
fi
exit 0
RCEOF
sudo chmod +x /etc/rc.local
echo "      SSH 호스트 키 재생성 설정 완료"

echo "[6/6] bash 히스토리 삭제..."
history -c
rm -f ~/.bash_history
rm -f /root/.bash_history
echo "      히스토리 삭제 완료"

echo ""
echo "======================================================"
echo "  준비 완료! 이제 SD카드 이미지를 생성할 수 있습니다."
echo "======================================================"
echo ""
echo "다음 단계 (이 라즈베리파이를 종료한 후 다른 PC에서 실행):"
echo ""
echo "1. 라즈베리파이 종료:"
echo "   sudo shutdown -h now"
echo ""
echo "2. SD카드를 PC에 연결 후 이미지 생성:"
echo "   Linux/Mac:"
echo "   sudo dd if=/dev/sdX of=unitank-image.img bs=4M status=progress"
echo "   sudo pishrink.sh unitank-image.img unitank-image-small.img"
echo ""
echo "   Windows:"
echo "   Win32DiskImager로 읽기 후 저장"
echo ""
echo "3. 배포 시 SD카드에 이미지 굽기:"
echo "   Raspberry Pi Imager > Use Custom > unitank-image-small.img"
echo ""
echo "4. 첫 부팅 후 브라우저에서:"
echo "   http://<라즈베리파이IP>:8000 접속 → 초기 설정 진행"
echo ""
