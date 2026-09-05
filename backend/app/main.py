import app.core.path_setup  # Ensure sys.path includes project root
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

import logging
from sqlalchemy import select
from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.models import Merchant, Customer, Transaction, RecoveryWorkflow, AuditLog, WebhookEvent, User
from app.api.v1 import api_router
from app.core.auth import ensure_initial_users
from app.api.v1.demo import perform_seed

logger = logging.getLogger("recoverai.startup")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize SQLite / PostgreSQL DB schema tables
    logger.info("Initializing database schema tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema tables verified/created.")
    
    # 2. Guarantee baseline demo users exist with verified password hashes
    async with AsyncSessionLocal() as session:
        try:
            await ensure_initial_users(session)
            logger.info("Demo users (admin@acrobatics.com, ops@acrobatics.com) successfully verified/seeded.")
        except Exception as e:
            logger.error("Error ensuring initial users: %s", str(e), exc_info=True)

    # 3. Initialize baseline dataset if unseeded
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Customer).where(Customer.id == "cust_aarav")
            res = await session.execute(stmt)
            if not res.scalar_one_or_none():
                logger.info("Populating initial baseline transaction/customer data...")
                await perform_seed(session)
                logger.info("Baseline demo dataset initialized.")
        except Exception as e:
            logger.error("Error populating baseline dataset: %s", str(e), exc_info=True)

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
    allow_origin_regex=r"^https://.*\.onrender\.com$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {
        "service": "RecoverAI Engine",
        "status": "online",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }

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
