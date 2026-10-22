from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.patch import PatchResponse


class UIElement(BaseModel):
    type: str  # button|input|modal|list|nav|other
    label: str
    state: str = "normal"  # normal|disabled|hidden|overlapped|misaligned|loading|error
    bbox: Optional[List[float]] = None  # [x, y, w, h] in normalized 0..1 or pixel coords


class Anomaly(BaseModel):
    kind: str  # layout_break|overlap|clipped|missing_element|wrong_state|empty_state|error_banner|other
    description: str
    confidence: float = 0.0


class VisualFindings(BaseModel):
    summary: str = ""
    visible_error_text: List[str] = Field(default_factory=list)
    ui_elements: List[UIElement] = Field(default_factory=list)
    anomalies: List[Anomaly] = Field(default_factory=list)
    likely_component_keywords: List[str] = Field(default_factory=list)
    image_quality: str = "good"  # good|low|irrelevant


class StackFrame(BaseModel):
    file: str
    line: Optional[int] = None
    column: Optional[int] = None
    function: Optional[str] = None
    raw: str = ""
    is_app_code: bool = True


class ErrorSignature(BaseModel):
    error_type: str
    message: str
    fingerprint: str


class LogFindings(BaseModel):
    error_signatures: List[ErrorSignature] = Field(default_factory=list)
    stack_frames: List[StackFrame] = Field(default_factory=list)
    first_error_timestamp: Optional[str] = None
    noise_filtered_count: int = 0
    raw_snippet: Optional[str] = None


class SuspectEvidence(BaseModel):
    type: str  # stack_frame | ui_label | semantic | git_recent | graph
    detail: str


class Suspect(BaseModel):
    file_path: str
    symbol: str
    lines: List[int] = Field(default_factory=lambda: [1, 1])
    score: float = 0.0  # Relative rank score (0.0 - 1.0), NOT a probability
    evidence: List[SuspectEvidence] = Field(default_factory=list)


class InvestigationStep(BaseModel):
    step: int
    thought: str
    tool: str
    tool_input: Optional[Dict[str, Any]] = None
    result_snippet: str


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    report_id: str
    status: str  # queued|running|completed|failed
    stage: str
    progress: int
    visual_findings: Optional[Dict[str, Any]] = None
    log_findings: Optional[Dict[str, Any]] = None
    suspects: Optional[List[Dict[str, Any]]] = None
    investigation_trace: Optional[List[Dict[str, Any]]] = None
    root_cause_hypothesis: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    finished_at: Optional[datetime] = None
    patches: List[PatchResponse] = []


class AnalysisFeedbackCreate(BaseModel):
    suspect_rank_correct: bool
    correct_file: Optional[str] = None


class AnalysisRerunRequest(BaseModel):
    w_dense: Optional[float] = None
    w_lex: Optional[float] = None
    w_stack: Optional[float] = None
    w_ui: Optional[float] = None
    w_git: Optional[float] = None
    w_graph: Optional[float] = None
