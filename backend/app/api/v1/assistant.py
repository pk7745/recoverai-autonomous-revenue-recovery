from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.agents.assistant import OperationsAssistant

router = APIRouter(prefix="/assistant", tags=["Operations Assistant"])

class AssistantQueryRequest(BaseModel):
    query: str
    context_workflow_id: Optional[str] = None

class AssistantQueryResponse(BaseModel):
    query: str
    summary: str
    observed_data: str
    ai_recommendation: str
    policy_decision: str
    final_outcome: str
    references: List[str]

@router.post("/query", response_model=AssistantQueryResponse)
async def query_operations_assistant(
    req: AssistantQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Processes natural language questions grounded strictly in live database records."""
    res = await OperationsAssistant.answer_query(
        db=db,
        query=req.query,
        context_workflow_id=req.context_workflow_id
    )
    return res
