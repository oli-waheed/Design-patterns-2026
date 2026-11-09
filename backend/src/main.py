
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from application.readings.sampler import SimulationSampler
from infrastructure.db import SessionLocal
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository
from infrastructure.settings import settings
from interfaces.api.automation import router as automation_router
from interfaces.api.devices import (
    actuator_router,
    router as devices_router,
)
from interfaces.api.health import router as health_router
from interfaces.api.locations import router as locations_router
from interfaces.api.overview import router as overview_router
from interfaces.api.sensors import router as sensors_router


async def run_simulation_sampler() -> None:
    while True:
        db = SessionLocal()

        try:
            device_repository = DeviceRepository(db)
            reading_repository = ReadingRepository(db)

            sampler = SimulationSampler(
                device_repository=device_repository,
                reading_repository=reading_repository,
            )

            sampler.sample_once()

        except Exception as exc:
            print(f"Simulation sampler error: {exc}")

        finally:
            db.close()

        await asyncio.sleep(5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    sampler_task = asyncio.create_task(run_simulation_sampler())

    try:
        yield
    finally:
        sampler_task.cancel()

        try:
            await sampler_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Smart Greenhouse API",
    description="API for the Smart Greenhouse application",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


# Read comma-separated origins from the root .env configuration.
allowed_origins = [
    origin.strip()
    for origin in settings.cors_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(health_router)
app.include_router(sensors_router)
app.include_router(locations_router)
app.include_router(automation_router)
app.include_router(devices_router)
app.include_router(actuator_router)
app.include_router(overview_router)


@app.get("/")
def root():
    return {
        "message": "Smart Greenhouse API",
        "api_reference": "/scalar",
        "openapi": "/openapi.json",
    }


@app.get("/scalar", include_in_schema=False)
def scalar():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )
