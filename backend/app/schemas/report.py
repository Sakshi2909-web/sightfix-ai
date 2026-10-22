from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: str
    storage_path: str
    mime: str
    meta_info: Optional[Dict[str, Any]] = None


class BugReportCreate(BaseModel):
    repo_id: str
    title: str
    description: str
    platform: Optional[str] = "web"


class BugReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    repo_id: str
    title: str
    description: str
    platform: str
    created_at: datetime
    attachments: List[AttachmentResponse] = []
