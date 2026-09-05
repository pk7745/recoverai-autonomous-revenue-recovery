from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.core.database import get_db
from app.models.recovery_workflow import RecoveryWorkflow
from app.models.transaction import Transaction
from app.schemas.recovery import (
    RecoveryWorkflowResponse,
    RecoveryPlanRequest,
    ManualApprovalRequest
)
from app.recovery.orchestrator import RecoveryOrchestrator
from app.core.enums import RecoveryState, ActorType
from app.audit.audit_service import AuditService

router = APIRouter(prefix="/recovery", tags=["Recovery Workflows"])
orchestrator = RecoveryOrchestrator()

@router.get("", response_model=List[RecoveryWorkflowResponse])
@router.get("/", response_model=List[RecoveryWorkflowResponse], include_in_schema=False)
async def list_recovery_workflows(
    state: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(RecoveryWorkflow)
        .options(
            selectinload(RecoveryWorkflow.transaction).selectinload(Transaction.customer)
        )
        .order_by(RecoveryWorkflow.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if state:
        stmt = stmt.where(RecoveryWorkflow.state == state)

    res = await db.execute(stmt)
    workflows = res.scalars().all()
    return workflows

@router.get("/{workflow_id}", response_model=RecoveryWorkflowResponse)
async def get_recovery_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(RecoveryWorkflow)
        .where(RecoveryWorkflow.id == workflow_id)
        .options(
            selectinload(RecoveryWorkflow.transaction).selectinload(Transaction.customer),
            selectinload(RecoveryWorkflow.transaction).selectinload(Transaction.merchant)
        )
    )
    res = await db.execute(stmt)
    workflow = res.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Recovery workflow not found")
    return workflow

@router.post("/{workflow_id}/plan", response_model=RecoveryWorkflowResponse)
async def plan_recovery_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        workflow = await orchestrator.plan_workflow(db, workflow_id)
        await db.commit()
        return workflow
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{workflow_id}/execute", response_model=RecoveryWorkflowResponse)
async def execute_recovery_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        workflow = await orchestrator.execute_workflow(db, workflow_id)
        await db.commit()
        return workflow
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{workflow_id}/approve", response_model=RecoveryWorkflowResponse)
async def approve_escalated_workflow(
    workflow_id: str,
    req: ManualApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(RecoveryWorkflow)
        .where(RecoveryWorkflow.id == workflow_id)
        .options(
            selectinload(RecoveryWorkflow.transaction).selectinload(Transaction.customer)
        )
    )
    res = await db.execute(stmt)
    workflow = res.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow.state = RecoveryState.POLICY_APPROVED.value
    if req.action_override:
        workflow.recommended_action = req.action_override.value

    await AuditService.log_event(
        db=db,
        actor=ActorType.MERCHANT_ADMIN,
        action="ESCALATION_MANUALLY_APPROVED",
        transaction_id=workflow.transaction_id,
        workflow_id=workflow.id,
        details={"notes": req.notes, "action": workflow.recommended_action}
    )

    # Immediately execute approved action
    workflow = await orchestrator.execute_workflow(db, workflow.id)
    await db.commit()
    return workflow

@router.post("/{workflow_id}/stop", response_model=RecoveryWorkflowResponse)
async def stop_recovery_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(RecoveryWorkflow)
        .where(RecoveryWorkflow.id == workflow_id)
        .options(
            selectinload(RecoveryWorkflow.transaction).selectinload(Transaction.customer)
        )
    )
    res = await db.execute(stmt)
    workflow = res.scalar_one_or_none()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow.state = RecoveryState.STOPPED.value
    workflow.stopping_rule_triggered = "Manually stopped by Merchant Operator"

    await AuditService.log_event(
        db=db,
        actor=ActorType.MERCHANT_ADMIN,
        action="WORKFLOW_MANUALLY_STOPPED",
        transaction_id=workflow.transaction_id,
        workflow_id=workflow.id,
        details={"reason": "Manual operator override"}
    )
    await db.commit()
    return workflow
