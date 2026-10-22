from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class RepoCreateGit(BaseModel):
    git_url: str
    branch: Optional[str] = "main"


class RepoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    source_type: str
    source_url: Optional[str] = None
    default_branch: str
    language_stats: Optional[Dict[str, Any]] = None
    index_status: str
    commit_sha: Optional[str] = None
    created_at: datetime


class RepoDetailResponse(RepoResponse):
    total_chunks: int = 0
    total_reports: int = 0
