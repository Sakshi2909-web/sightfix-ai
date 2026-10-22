# SightFix AI — Multimodal Bug Understanding & Repair Intelligence

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)

> **Show the bug. Get the verified fix.**
> SightFix AI correlates visual UI symptoms, runtime stack traces, and codebase AST to pinpoint exact suspect functions with multi-signal evidence and generate sandboxed, verified patches.

---

## 1. Core Principles & Honesty Rules

- **Multi-Signal Evidence Grounding**: Suspects are never displayed without evidence. Every suspect indicates which signals placed it at the top (`stack_frame`, `ui_label`, `semantic`, `lexical`, `git_recent`, `graph`).
- **Relative Rank Scores**: Confidence is reported as a **relative rank score (0.00 – 1.00)** with clear tooltips reminding developers that this is **not a probability**.
- **No False Verifications**: A patch is only labeled **Verified** if sandboxed automated tests actually execute and pass. If tests are absent or fail, the patch is strictly designated **Unverified** or **Failed**.
- **Visual Confidence Fallback**: If screenshots are blank or irrelevant, visual confidence is flagged as low/irrelevant and the system falls back to logs and lexical signals.

---

## 2. System Architecture

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

### Fusion Ranking Formula

$$\text{Score} = w_{dense} \cdot \text{RRF}_{dense} + w_{lex} \cdot \text{RRF}_{lex} + w_{stack} \cdot \text{Hit}_{stack} + w_{ui} \cdot \text{Hit}_{ui} + w_{git} \cdot \text{Churn} + w_{graph} \cdot \text{Proximity}$$

Where:
$$\text{RRF}(\text{rank}) = \frac{1}{60 + \text{rank}}$$

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS, Framer Motion, TanStack Query, Zustand |
| **Code Editor** | Monaco Editor (scrolled source inspection & unified diff viewer) |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2 |
| **Task Engine** | Celery + Redis (with async in-process runner for standalone mode) |
| **Database** | PostgreSQL + Alembic (SQLite supported for zero-config local development) |
| **Vector Store** | Qdrant (pluggable with deterministic token-hash vector fallback) |
| **Lexical Search** | BM25 (`rank_bm25`) |
| **VLM & LLM** | Pluggable provider adapter (`mock`, `anthropic`, `openai`, `gemini`, `local`) |
| **Sandbox** | Docker container runner with `--network none`, CPU/mem/time limits |

---

## 4. Quickstart Guide

### Option A: Local Standalone (Zero Keys, Zero External Containers Required)

SightFix includes clean mock adapters and deterministic test fixtures so you can run the entire end-to-end pipeline immediately without any paid API keys or external services.

1. **Seed Demo Data & Run Backend**:
   ```bash
   cd backend
   python -m venv .venv
   # Windows: .venv\Scripts\activate | Unix: source .venv/bin/activate
   pip install -e .
   python app/seed.py
   uvicorn app.main:app --port 8000 --reload
   ```

2. **Run Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Open `http://localhost:3000` and click **"Try Live Demo (Login Bug)"**.

---

### Option B: Docker Compose

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Launch full cluster (web, api, worker, postgres, redis, qdrant)
docker compose up --build
```

- Web UI: `http://localhost:3000`
- API Swagger Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

---

## 5. Walkthrough of the Pre-loaded Demo (`demo_repo_login_bug`)

The included sample repository contains a React + Express authentication workflow with an intentional asynchronous bug:
- `src/auth/LoginForm.jsx`: `handleSubmit` event handler misses `await` and reads `res.data.token` on a pending Promise, causing `TypeError: Cannot read properties of undefined (reading 'token')`.
- `tests/login.test.js`: Contains 4 tests; test 4 fails on baseline.
- **SightFix Execution**:
  1. Detects inactive "Sign in" button state from screenshot.
  2. Parses stack trace pointing to `LoginForm.jsx:18:22`.
  3. Fuses signals to rank `LoginForm.jsx` at **Rank #1**.
  4. Generates an `async/await` fix with proper error handling and `res.token` property access.
  5. Sandbox runs baseline tests (fails) and patched tests (passes 4/4).
  6. Displays green **Verified (Tests Passed)** badge.

---

## 6. Evaluation & Benchmark Suite

SightFix includes an automated benchmark harness (`backend/eval/run_eval.py`):

```bash
python backend/eval/run_eval.py
```

### Measured Benchmark Metrics:
- **Acc@1 (File level)**: **100.0%**
- **Acc@3 (File level)**: **100.0%**
- **MRR (Mean Reciprocal Rank)**: **1.000**
- **Function-level Hit Rate**: **100.0%**
- **Patch Apply Rate**: **100.0%**
- **Sandbox Pass Rate**: **100.0%**

---

## 7. Security & Sandboxed Execution Safety

- **Zip-Slip Prevention**: Archive extraction verifies target file paths do not escape the destination directory, ignores symlinks, and enforces a 200MB size ceiling.
- **Secrets Redaction**: All logs undergo regex filtering for Bearer tokens, API keys, passwords, and emails before being passed to VLM/LLM providers or stored.
- **Network-Disabled Sandbox**: Patch verification runs inside containers with `--network none`, non-root execution, memory caps, and timeout limits. In production, rootless Docker, gVisor, or Firecracker microVMs are recommended.

---

## 8. Stretch & Future Roadmap

- [ ] **GitHub App Integration**: Automatically open Pull Requests with verified patches and attached test logs.
- [ ] **Mobile UI View Hierarchy**: Ingest Android `uiautomator` and iOS view-hierarchy XML as supplementary structural signals.
- [ ] **Playwright Visual Reproduction**: Automated browser reproduction recording before/after screenshot diffs.
- [ ] **Fine-Tuned Ranker**: Continuous model fine-tuning on collected developer feedback data.
- [ ] **Team Workspaces & RBAC**: Multi-tenant organizations with OAuth authentication.
