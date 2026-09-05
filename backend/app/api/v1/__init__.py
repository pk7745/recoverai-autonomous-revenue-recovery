from fastapi import APIRouter
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.recovery import router as recovery_router
from app.api.v1.policies import router as policies_router
from app.api.v1.safety import router as safety_router
from app.api.v1.experiments import router as experiments_router
from app.api.v1.audit import router as audit_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.demo import router as demo_router
from app.api.v1.auth import router as auth_router
from app.api.v1.events import router as events_router
from app.api.v1.assistant import router as assistant_router

api_router = APIRouter()
api_router.include_router(dashboard_router)
api_router.include_router(recovery_router)
api_router.include_router(policies_router)
api_router.include_router(safety_router)
api_router.include_router(experiments_router)
api_router.include_router(audit_router)
api_router.include_router(webhooks_router)
api_router.include_router(demo_router)
api_router.include_router(auth_router)
api_router.include_router(events_router)
api_router.include_router(assistant_router)
