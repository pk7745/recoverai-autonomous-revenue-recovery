import app.core.path_setup  # Ensure sys.path includes project root
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.models import Merchant, Customer, Transaction, RecoveryWorkflow, AuditLog, WebhookEvent, User
from app.api.v1 import api_router
from app.api.v1.demo import seed_demo_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite / PostgreSQL DB schema tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Auto-seed demo dataset in development/demo mode only
    if settings.ENVIRONMENT != "production":
        async with AsyncSessionLocal() as session:
            try:
                await seed_demo_database(session)
            except Exception:
                pass

    yield
    await engine.dispose()

app = FastAPI(
    title="RecoverAI - AI Revenue Recovery Engine",
    description="Orchestration platform for detecting, diagnosing, and recovering failed Razorpay payment revenue.",
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS configuration for frontend
origins = settings.get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "RecoverAI Engine",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=(settings.ENVIRONMENT != "production"))
