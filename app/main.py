import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db

# Import API routers
from app.api.v1.auth import router as auth_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.signals import router as signals_router
from app.api.v1.investigations import router as investigations_router
from app.api.v1.actions import router as actions_router
from app.api.v1.agent import router as agent_router
from app.api.v1.audit import router as audit_router
from app.api.v1.sync import router as sync_router
from app.api.v1.settings import router as settings_router
from app.api.v1.emails import router as emails_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schemas cleanly (no fake demo seeding)
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Live Multi-Agent AI Operating Layer for Startups",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers under /api/v1
api_prefix = "/api/v1"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(workspaces_router, prefix=api_prefix)
app.include_router(integrations_router, prefix=api_prefix)
app.include_router(signals_router, prefix=api_prefix)
app.include_router(investigations_router, prefix=api_prefix)
app.include_router(actions_router, prefix=api_prefix)
app.include_router(agent_router, prefix=api_prefix)
app.include_router(audit_router, prefix=api_prefix)
app.include_router(sync_router, prefix=api_prefix)
app.include_router(settings_router, prefix=api_prefix)
app.include_router(emails_router, prefix=api_prefix)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "has_gemini_key": bool(settings.GOOGLE_AI_STUDIO_API_KEY and not settings.GOOGLE_AI_STUDIO_API_KEY.startswith("your_")),
        "environment": settings.ENVIRONMENT
    }

def get_frontend_dir():
    candidates = [
        os.path.abspath("static"),
        os.path.abspath("frontend/out"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "out"),
        os.path.abspath("out"),
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.exists(os.path.join(c, "index.html")):
            return c
    return None

frontend_dir = get_frontend_dir()


if frontend_dir:
    next_dir = os.path.join(frontend_dir, "_next")
    if os.path.exists(next_dir):
        app.mount("/_next", StaticFiles(directory=next_dir), name="_next")

    @app.get("/", tags=["Frontend"])
    async def serve_root():
        index_path = os.path.join(frontend_dir, "index.html")
        return FileResponse(index_path)

    @app.get("/{full_path:path}", tags=["Frontend"])
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path in ["docs", "redoc", "openapi.json", "health"]:
            return None
        file_path = os.path.join(frontend_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.isfile(index_path):
            return FileResponse(index_path)
        return {"message": "StartupOps AI Ready", "docs": "/docs"}
else:
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "message": "Welcome to StartupOps AI Live Engine",
            "docs": "/docs",
            "health": "/health"
        }
