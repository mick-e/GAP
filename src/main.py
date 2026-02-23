from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.config import get_settings


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.database import create_tables, dispose_engine
    await create_tables()
    yield
    await dispose_engine()


app = FastAPI(
    title="BHAPI - GitHub Reports API",
    description="Generate comprehensive reports for GitHub organization repositories",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
from src.api import router as api_router  # noqa: E402
from src.auth.router import router as auth_router  # noqa: E402
from src.webhooks.router import router as webhooks_router  # noqa: E402
from src.contributors.router import router as contributors_router  # noqa: E402
from src.trends.router import router as trends_router  # noqa: E402
from src.scheduler.router import router as scheduler_router  # noqa: E402
from src.teams.router import router as teams_router  # noqa: E402

app.include_router(api_router)
app.include_router(auth_router)
app.include_router(webhooks_router)
app.include_router(contributors_router)
app.include_router(trends_router)
app.include_router(scheduler_router)
app.include_router(teams_router)


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
        "name": "BHAPI - GitHub Reports API",
        "version": "0.2.0",
        "organization": settings.github_org,
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
