export interface Repo {
  id: string;
  name: string;
  source_type: "zip" | "git";
  source_url?: string | null;
  default_branch: string;
  language_stats?: Record<string, number> | null;
  index_status: "pending" | "indexing" | "ready" | "failed";
  commit_sha?: string | null;
  created_at: string;
  total_chunks?: number;
  total_reports?: number;
}

export interface UIElement {
  type: string;
  label: string;
  state: "normal" | "disabled" | "hidden" | "overlapped" | "misaligned" | "loading" | "error";
  bbox?: [number, number, number, number] | null;
}

export interface Anomaly {
  kind: string;
  description: string;
  confidence: number;
}

export interface VisualFindings {
  summary: string;
  visible_error_text: string[];
  ui_elements: UIElement[];
  anomalies: Anomaly[];
  likely_component_keywords: string[];
  image_quality: "good" | "low" | "irrelevant";
}

export interface StackFrame {
  file: string;
  line?: number | null;
  column?: number | null;
  function?: string | null;
  raw: string;
  is_app_code: boolean;
}

export interface ErrorSignature {
  error_type: string;
  message: string;
  fingerprint: string;
}

export interface LogFindings {
  error_signatures: ErrorSignature[];
  stack_frames: StackFrame[];
  first_error_timestamp?: string | null;
  noise_filtered_count: number;
  raw_snippet?: string | null;
}

export interface SuspectEvidence {
  type: "stack_frame" | "ui_label" | "semantic" | "lexical" | "git_recent" | "graph";
  detail: string;
}

export interface Suspect {
  file_path: string;
  symbol: string;
  lines: [number, number];
  score: number; // 0.0 - 1.0 (relative rank score)
  evidence: SuspectEvidence[];
}

export interface InvestigationStep {
  step: number;
  thought: string;
  tool: string;
  tool_input?: any;
  result_snippet: string;
}

export interface Patch {
  id: string;
  analysis_id: string;
  target_files: string[];
  diff_text: string;
  rationale: string;
  verification_status: "unverified" | "passed" | "failed" | "error";
  test_output?: string | null;
  sandbox_meta?: Record<string, any> | null;
  suggested_tests?: string | null;
  created_at: string;
}

export interface Analysis {
  id: string;
  report_id: string;
  status: "queued" | "running" | "completed" | "failed";
  stage: string;
  progress: number;
  visual_findings?: VisualFindings | null;
  log_findings?: LogFindings | null;
  suspects?: Suspect[] | null;
  investigation_trace?: InvestigationStep[] | null;
  root_cause_hypothesis?: string | null;
  error?: string | null;
  created_at: string;
  finished_at?: string | null;
  patches: Patch[];
}

export interface BugReport {
  id: string;
  repo_id: string;
  title: string;
  description: string;
  platform: string;
  created_at: string;
}
