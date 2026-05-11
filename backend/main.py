from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.models.database import init_db
from backend.scheduler import start_scheduler, stop_scheduler
from backend.api.routes import bmc, heat_exchanger, immersion_tank, pdu

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(title="Loveworm 모니터링 시스템", lifespan=lifespan)

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
