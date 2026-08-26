from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from contextlib import asynccontextmanager
from pathlib import Path

from backend.models.database import init_db
from backend.scheduler import start_scheduler, stop_scheduler
from backend.api.routes import bmc, heat_exchanger, immersion_tank, pdu
from backend.api.routes.setup import router as setup_router
from backend.api.routes.system import router as system_router

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


@app.middleware("http")
async def setup_redirect_middleware(request: Request, call_next):
    from backend.config import settings
    path = request.url.path
    skip = path.startswith("/api/setup") or path == "/setup" or path.startswith("/assets")
    if not settings.CONFIGURED and not skip:
        return RedirectResponse("/setup")
    return await call_next(request)


app.include_router(setup_router)
app.include_router(system_router)
app.include_router(bmc.router)
app.include_router(heat_exchanger.router)
app.include_router(immersion_tank.router)
app.include_router(pdu.router)


@app.get("/api/health")
async def health():
    from backend.config import settings
    return {"status": "ok", "service": "loveworm-monitor", "unit": settings.UNIT_NAME}


# 프론트엔드 정적 파일 서빙
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse(FRONTEND_DIST / "index.html")
