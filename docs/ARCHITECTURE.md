# SightFix AI Architecture

## 1. System Overview

SightFix AI is a multimodal bug understanding, localization, and automated repair platform. It correlates visual symptoms (screenshots, screen recordings) and runtime telemetry (stack traces, server/console logs) with codebase AST and history to pinpoint suspects and synthesize verified patches.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Next.js 14 Frontend                             │
│       Landing · New Analysis · Analysis Detail · Repos · History       │
└───────────────────▲────────────────────────────────┬───────────────────┘
                    │ SSE / Stream                   │ REST
┌───────────────────┴────────────────────────────────▼───────────────────┐
│                          FastAPI Backend                               │
│            /repos  /reports  /analyses  /patches  /health              │
└───────────────────▲────────────────────────────────┬───────────────────┘
                    │                                │
┌───────────────────┴──────────┐        ┌────────────▼───────────────────┐
│   Task Runner / Orchestrator │        │      Data & Storage Tier       │
│  (Celery / Background Tasks) │◄──────►│  PostgreSQL / SQLite (Metadata)│
└───────────────────┬──────────┘        │  Qdrant (Vectors)              │
                    │                   │  Local / S3 Blob Store         │
                    │                   └────────────────────────────────┘
┌───────────────────▼────────────────────────────────────────────────────┐
│                       9-Stage Analysis Pipeline                        │
│                                                                        │
│ 1. Ingest: Validate inputs, extract video keyframes                    │
│ 2. Visual Understanding: OCR + VLM element/anomaly detection           │
│ 3. Log Analysis: Regex parsing of multi-language stack traces & errors │
│ 4. Repo Indexing: AST symbol chunking + BM25 + Vector embedding        │
│ 5. Hybrid Retrieval: Dense + BM25 + Stack Frames + UI Labels + Git     │
│ 6. Fusion Ranking: Reciprocal Rank Fusion + Multi-channel weighting    │
│ 7. Agentic Investigation: RAG tool loop validating hypotheses          │
│ 8. Patch Generation: Minimal unified diff + `git apply --check` retry  │
│ 9. Sandbox Verification: Docker execution comparing baseline vs patched│
└────────────────────────────────────────────────────────────────────────┘
```

## 2. Multi-Signal Fusion Ranking

SightFix fuses signals across multiple modalities:
- **Dense semantic retrieval**: VLM UI summary + anomaly text mapped to code chunks.
- **Lexical BM25**: Extracted OCR labels, error messages, and component tokens.
- **Stack Trace direct match**: File paths and line numbers parsed from logs.
- **UI string match**: Code string literals matching visible button/input text.
- **Git recency**: Recency weight from git commit history and churn.
- **Graph proximity**: 1-hop callers and import dependency graph expansion.

Composite score formula:
$$Score = w_{dense} \cdot RRF_{dense} + w_{lex} \cdot RRF_{lex} + w_{stack} \cdot Hit_{stack} + w_{ui} \cdot Hit_{ui} + w_{git} \cdot Recency + w_{graph} \cdot Proximity$$

## 3. Sandboxed Execution Safety
- Docker containers run with `--network none`, strict CPU (1–2 cores) and memory (1–2 GB) constraints.
- Execution timeout (default 180s).
- All diffs are pre-validated with `git apply --check` before applying.
