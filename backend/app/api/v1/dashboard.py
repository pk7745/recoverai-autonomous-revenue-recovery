from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.dashboard import DashboardOverviewResponse
from app.analytics.metrics_service import MetricsService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(db: AsyncSession = Depends(get_db)):
    return await MetricsService.get_dashboard_overview(db)
