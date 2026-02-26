from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.creators import router as creators_router
from app.api.ranking import router as ranking_router
from app.api.recommendations import router as recommendations_router
from app.api.subscriptions import router as subscriptions_router
from app.config import get_settings
from app.database import engine

settings = get_settings()

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage the async engine lifecycle (important for Vercel serverless)."""
    yield
    await engine.dispose()


app = FastAPI(
    title="PickRank API",
    description="Automated stock recommendation tracking for DACH retail investors.",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# All routes prefixed with /api
app.include_router(creators_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(ranking_router, prefix="/api")
app.include_router(subscriptions_router, prefix="/api")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
