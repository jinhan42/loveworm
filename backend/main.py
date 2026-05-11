from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from backend.models.database import init_db
from backend.scheduler import start_scheduler, stop_scheduler
from backend.api.routes import bmc, heat_exchanger, immersion_tank, pdu

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(title="UniTank 모니터링 시스템", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bmc.router)
app.include_router(heat_exchanger.router)
app.include_router(immersion_tank.router)
app.include_router(pdu.router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "loveworm-monitor"}

# 프론트엔드 정적 파일 서빙
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse(FRONTEND_DIST / "index.html")
