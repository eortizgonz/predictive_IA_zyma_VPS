from typing import Literal
from pydantic import BaseModel, Field


class CopilotRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    profile: Literal["operations", "finance", "technology"] = "operations"
    machine_id: str | None = None
    conversation_id: str | None = None


class WorkOrderPreviewRequest(BaseModel):
    machine_id: str
    estimated_cost: float | None = None
