# Loveworm 모니터링 시스템

Raspberry Pi 5 기반의 액침냉각 서버 통합 모니터링 시스템

## 모니터링 항목

| 항목 | 수집 데이터 | 프로토콜 |
|------|------------|---------|
| 서버 BMC | CPU 온도, PSU 전력/전압/전류 | IPMI / Redfish API |
| 열교환기 | 물 LPM, 냉각유 LPM | Modbus RTU / TCP |
| 이머전 탱크 | 상/하층 온도, 냉각유 유량 | Modbus RTU / TCP |
| PDU | 전체 전력, 아울렛별 전력 | SNMP / Modbus |

## 폴더 구조

```
loveworm/
├── backend/          # FastAPI 서버 + 데이터 수집기
├── frontend/         # React.js 웹 UI (한국어/영어)
├── sensors/          # 권장 센서 목록 및 배선 가이드
├── docs/             # 설치 및 설정 문서
└── scripts/          # Raspberry Pi 자동 설치 스크립트
```

## 빠른 시작 (Raspberry Pi)

```bash
git clone https://github.com/jinhan42/loveworm.git
cd loveworm
chmod +x scripts/install.sh
./scripts/install.sh
```

설치 후 `backend/.env` 파일에서 실제 장비 IP와 인증 정보를 설정하세요.

## 접속

- 웹 UI: `http://라즈베리파이IP:8000`
- API 문서: `http://라즈베리파이IP:8000/docs`
