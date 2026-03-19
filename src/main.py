from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.config import get_settings
from src.logging_config import setup_logging
from src.middleware import limiter, RequestLoggingMiddleware


settings = get_settings()
setup_logging(settings.debug)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.database import create_tables, dispose_engine
    from src.cache import init_redis, close_redis
    from src.scheduler.background import start_scheduler, stop_scheduler
    await create_tables()
    await init_redis()
    await start_scheduler()
    yield
    await stop_scheduler()
    await close_redis()
    await dispose_engine()


app = FastAPI(
    title="GAP - GitHub Analytics Platform",
    description="Generate comprehensive reports for GitHub organization repositories",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Routers
from src.api import router as api_router  # noqa: E402
from src.auth.router import router as auth_router  # noqa: E402
from src.webhooks.router import router as webhooks_router  # noqa: E402
from src.contributors.router import router as contributors_router  # noqa: E402
from src.trends.router import router as trends_router  # noqa: E402
from src.scheduler.router import router as scheduler_router  # noqa: E402
from src.teams.router import router as teams_router  # noqa: E402
from src.metrics.router import router as metrics_router  # noqa: E402
from src.exports.router import router as exports_router  # noqa: E402
from src.audit import router as audit_router  # noqa: E402
from src.oauth.router import router as oauth_router  # noqa: E402
from src.notifications.router import router as notifications_router  # noqa: E402

app.include_router(api_router)
app.include_router(auth_router)
app.include_router(webhooks_router)
app.include_router(contributors_router)
app.include_router(trends_router)
app.include_router(scheduler_router)
app.include_router(teams_router)
app.include_router(metrics_router)
app.include_router(exports_router)
app.include_router(audit_router)
app.include_router(oauth_router)
app.include_router(notifications_router)


# SPA catch-all: serve dashboard if built
dashboard_dist = Path(__file__).parent.parent / "dashboard" / "dist"
if dashboard_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(dashboard_dist / "assets")), name="assets")

    from fastapi.responses import FileResponse

    @app.get("/app/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(str(dashboard_dist / "index.html"))


@app.get("/")
async def root():
    return {
        "name": "GAP - GitHub Analytics Platform",
        "version": "0.2.0",
        "organization": settings.github_org,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    checks = {"status": "healthy"}

    # Check database connectivity
    try:
        from src.database import get_engine
        from sqlalchemy import text
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
        checks["status"] = "degraded"

    # Check Redis connectivity
    try:
        from src.cache import get_redis
        redis = get_redis()
        if redis:
            await redis.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "not configured"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    if checks["database"] != "ok":
        from fastapi.responses import JSONResponse
        return JSONResponse(content=checks, status_code=503)

    return checks


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
