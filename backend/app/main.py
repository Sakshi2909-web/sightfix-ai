from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api import repos, reports, analyses, patches, stream


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables are created on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="SightFix AI API",
    description="Multimodal Bug Understanding & Repair Intelligence Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(repos.router)
app.include_router(reports.router)
app.include_router(analyses.router)
app.include_router(patches.router)
app.include_router(stream.router)


@app.get("/api/health", tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "service": "SightFix AI Backend",
        "version": "0.1.0",
        "providers": {
            "vlm": settings.VLM_PROVIDER,
            "llm": settings.LLM_PROVIDER,
            "embedding": settings.EMBEDDING_PROVIDER,
        },
        "sandbox": {
            "timeout_sec": settings.SANDBOX_TIMEOUT_SEC,
            "mem_mb": settings.SANDBOX_MEM_MB,
        },
    }
