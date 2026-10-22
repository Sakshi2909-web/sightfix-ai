from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class PatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    analysis_id: str
    target_files: List[str]
    diff_text: str
    rationale: str
    verification_status: str  # unverified | passed | failed | error
    test_output: Optional[str] = None
    sandbox_meta: Optional[Dict[str, Any]] = None
    suggested_tests: Optional[str] = None
    created_at: datetime


class PatchRegenerateRequest(BaseModel):
    feedback: str
