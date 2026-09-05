from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.audit import SafetyOverviewResponse
from app.analytics.metrics_service import MetricsService

router = APIRouter(prefix="/safety", tags=["Safety Center"])

@router.get("/overview", response_model=SafetyOverviewResponse)
async def get_safety_overview(db: AsyncSession = Depends(get_db)):
    return await MetricsService.get_safety_overview(db)
