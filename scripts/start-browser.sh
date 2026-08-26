#!/bin/bash
# UniTank 브라우저 자동 실행 스크립트
# 서버가 준비될 때까지 대기 후 Chromium 키오스크 모드로 실행

# 화면 보호기 / 절전 비활성화
xset s off
xset s noblank
xset -dpms

# 서버 준비 대기 (최대 60초)
echo "UniTank 서버 대기 중..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "서버 준비 완료!"
        break
    fi
    sleep 2
done

# Chromium 키오스크 모드 실행
chromium \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-translate \
    --no-first-run \
    --fast \
    --fast-start \
    --disable-features=TranslateUI,Translate \
    --touch-events=enabled \
    --incognito \
    http://localhost:8000
