from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.models.merchant import Merchant
from app.models.user import User
from app.core.auth import get_current_user, require_role
from app.schemas.policy import MerchantPolicyResponse, UpdateMerchantPolicyRequest
from app.audit.audit_service import AuditService
from app.core.enums import ActorType

router = APIRouter(prefix="/policies", tags=["Policies"])

@router.get("", response_model=MerchantPolicyResponse)
async def get_merchant_policy(db: AsyncSession = Depends(get_db)):
    stmt = select(Merchant).limit(1)
    res = await db.execute(stmt)
    merchant = res.scalar_one_or_none()
    if not merchant:
        # Fallback default
        return MerchantPolicyResponse(
            merchant_id="merch_default",
            merchant_name="Demo Merchant Enterprise",
            autonomous_limit=5000.0,
            max_retries=2,
            min_retry_interval_mins=30,
            risk_threshold=0.70
        )
    return MerchantPolicyResponse(
        merchant_id=merchant.id,
        merchant_name=merchant.name,
        autonomous_limit=merchant.autonomous_limit,
        max_retries=merchant.max_retries,
        min_retry_interval_mins=merchant.min_retry_interval_mins,
        risk_threshold=merchant.risk_threshold
    )

@router.put("", response_model=MerchantPolicyResponse)
async def update_merchant_policy(
    req: UpdateMerchantPolicyRequest,
    current_user: User = Depends(require_role(["MERCHANT_ADMIN"])),
    db: AsyncSession = Depends(get_db)
):

    stmt = select(Merchant).limit(1)
    res = await db.execute(stmt)
    merchant = res.scalar_one_or_none()
    if not merchant:
        merchant = Merchant(
            id="merch_default",
            name="Demo Merchant Enterprise",
            api_key_id="rzp_test_key",
            webhook_secret="whsec_secret"
        )
        db.add(merchant)

    if req.autonomous_limit is not None:
        merchant.autonomous_limit = req.autonomous_limit
    if req.max_retries is not None:
        merchant.max_retries = req.max_retries
    if req.min_retry_interval_mins is not None:
        merchant.min_retry_interval_mins = req.min_retry_interval_mins
    if req.risk_threshold is not None:
        merchant.risk_threshold = req.risk_threshold

    await AuditService.log_event(
        db=db,
        actor=ActorType.MERCHANT_ADMIN,
        action="MERCHANT_POLICIES_UPDATED",
        details={
            "autonomous_limit": merchant.autonomous_limit,
            "max_retries": merchant.max_retries,
            "risk_threshold": merchant.risk_threshold,
            "updated_by": current_user.email if current_user else "admin"
        }
    )

    await db.commit()
    return MerchantPolicyResponse(
        merchant_id=merchant.id,
        merchant_name=merchant.name,
        autonomous_limit=merchant.autonomous_limit,
        max_retries=merchant.max_retries,
        min_retry_interval_mins=merchant.min_retry_interval_mins,
        risk_threshold=merchant.risk_threshold
    )
