from fastapi import APIRouter, Depends, Request, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json

from app.core.database import get_db
from app.schemas.webhook import WebhookResponse
from app.webhooks.webhook_handler import WebhookHandler

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/razorpay", response_model=WebhookResponse)
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    db: AsyncSession = Depends(get_db)
):
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=401,
            detail="Missing required X-Razorpay-Signature header"
        )

    raw_body = await request.body()
    try:
        payload_data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    success, msg, details = await WebhookHandler.process_webhook(
        db=db,
        raw_body=raw_body,
        signature=x_razorpay_signature,
        payload_data=payload_data
    )
    
    if not success:
        await db.commit()
        raise HTTPException(
            status_code=401,
            detail=msg
        )

    await db.commit()

    return WebhookResponse(
        status="success",
        message=msg,
        event_id=details.get("event_id", "evt_unknown"),
        duplicate=details.get("is_duplicate", False),
        action_taken=details.get("event_type", "none")
    )
