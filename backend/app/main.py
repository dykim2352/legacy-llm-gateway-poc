from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.legacy import router as legacy_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.ws import router as ws_router
from app.core.config import settings
from app.core.database import init_db
from app.core.middleware import record_http_metrics


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Personal PoC for a legacy-system-integrated LLM Gateway.",
        lifespan=lifespan,
    )
    app.middleware("http")(record_http_metrics)
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(jobs_router)
    app.include_router(legacy_router)
    app.include_router(admin_router)
    app.include_router(ws_router)
    app.include_router(health_router)
    app.include_router(metrics_router)
    return app


app = create_app()
