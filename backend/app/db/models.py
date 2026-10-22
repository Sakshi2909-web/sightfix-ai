import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Repo(Base):
    __tablename__ = "repos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "zip" | "git"
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    local_path: Mapped[str] = mapped_column(String(512), nullable=False)
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    language_stats: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    index_status: Mapped[str] = mapped_column(String(30), default="pending")  # pending|indexing|ready|failed
    commit_sha: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    chunks: Mapped[List["CodeChunk"]] = relationship("CodeChunk", back_populates="repo", cascade="all, delete-orphan")
    reports: Mapped[List["BugReport"]] = relationship("BugReport", back_populates="repo", cascade="all, delete-orphan")


class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    repo_id: Mapped[str] = mapped_column(String(36), ForeignKey("repos.id", ondelete="CASCADE"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    symbol_name: Mapped[str] = mapped_column(String(255), nullable=False)
    symbol_type: Mapped[str] = mapped_column(String(50), nullable=False)  # function|class|method|component|module
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="unknown")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qdrant_point_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    repo: Mapped["Repo"] = relationship("Repo", back_populates="chunks")


class BugReport(Base):
    __tablename__ = "bug_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    repo_id: Mapped[str] = mapped_column(String(36), ForeignKey("repos.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(50), default="web")  # web|android|ios|desktop|backend
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    repo: Mapped["Repo"] = relationship("Repo", back_populates="reports")
    attachments: Mapped[List["Attachment"]] = relationship("Attachment", back_populates="report", cascade="all, delete-orphan")
    analyses: Mapped[List["Analysis"]] = relationship("Analysis", back_populates="report", cascade="all, delete-orphan")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("bug_reports.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(30), nullable=False)  # screenshot|video|log
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime: Mapped[str] = mapped_column(String(100), default="application/octet-stream")
    meta_info: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    report: Mapped["BugReport"] = relationship("BugReport", back_populates="attachments")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("bug_reports.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="queued")  # queued|running|completed|failed
    stage: Mapped[str] = mapped_column(String(50), default="Ingest")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    visual_findings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    log_findings: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    suspects: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    investigation_trace: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    root_cause_hypothesis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    report: Mapped["BugReport"] = relationship("BugReport", back_populates="analyses")
    patches: Mapped[List["Patch"]] = relationship("Patch", back_populates="analysis", cascade="all, delete-orphan")
    feedbacks: Mapped[List["AnalysisFeedback"]] = relationship("AnalysisFeedback", back_populates="analysis", cascade="all, delete-orphan")


class Patch(Base):
    __tablename__ = "patches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    target_files: Mapped[list] = mapped_column(JSON, default=list)
    diff_text: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(30), default="unverified")  # unverified|passed|failed|error
    test_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sandbox_meta: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    suggested_tests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="patches")


class AnalysisFeedback(Base):
    __tablename__ = "analysis_feedbacks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    analysis_id: Mapped[str] = mapped_column(String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    suspect_rank_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    correct_file: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="feedbacks")
