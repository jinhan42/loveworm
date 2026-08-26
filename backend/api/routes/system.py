from fastapi import APIRouter
import asyncio
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

router = APIRouter(prefix="/api/system", tags=["system"])

RTC_DATE = Path("/sys/class/rtc/rtc0/date")
RTC_TIME = Path("/sys/class/rtc/rtc0/time")
LOCAL_TZ = ZoneInfo("Asia/Seoul")


@router.get("/rtc-time")
async def get_rtc_time():
    rtc_date = RTC_DATE.read_text().strip()
    rtc_time = RTC_TIME.read_text().strip()
    utc_dt = datetime.strptime(f"{rtc_date} {rtc_time}", "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    local_dt = utc_dt.astimezone(LOCAL_TZ)
    return {"datetime": local_dt.strftime("%Y-%m-%d %H:%M")}


@router.post("/show-desktop")
async def show_desktop():
    async def _switch():
        await asyncio.sleep(1)
        # Chromium 키오스크 종료
        subprocess.run(["pkill", "-f", "chromium.*kiosk"])
        await asyncio.sleep(1)
        # wf-panel 재시작 (lwrespawn이 자동으로 다시 띄워줌)
        subprocess.run(["pkill", "wf-panel-pi"])
    asyncio.create_task(_switch())
    return {"ok": True}
