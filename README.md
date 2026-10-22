# SightFix AI — Multimodal Bug Understanding & Repair Intelligence

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)

> **Show the bug. Get the verified fix.**

SightFix AI is a multimodal bug-understanding and repair assistant. It combines visual UI symptoms, runtime stack traces, and repository code structure to rank likely fault locations, investigate hypotheses with retrieval-augmented generation (RAG), and propose patches that can be tested in a sandbox.

> **Verification note:** A patch should be described as verified only when the configured tests actually run and pass. Benchmark values and demo outcomes should be reported only after running the included evaluation against the current code.

---

## Contents

- [Why SightFix AI?](#why-sightfix-ai)
- [Core Principles](#core-principles)
- [System Architecture](#system-architecture)
- [Analysis Pipeline](#analysis-pipeline)
- [Technology Stack](#technology-stack)
- [Quickstart](#quickstart)
- [Docker Compose](#docker-compose)
- [Demo Workflow](#demo-workflow)
- [Evaluation](#evaluation)
- [Security Considerations](#security-considerations)
- [Roadmap](#roadmap)

## Why SightFix AI?

Debugging often requires developers to correlate multiple sources of evidence: what the user saw, what the runtime logged, and what the code is doing. SightFix AI brings these signals together to help developers investigate bugs more efficiently.

### Key capabilities

- **Multimodal input:** use screenshots or video keyframes alongside error messages and stack traces.
- **Code-aware retrieval:** combine lexical search, vector retrieval, stack-frame matching, UI labels, and repository structure.
- **Evidence-grounded ranking:** show why a file or function was ranked as a likely suspect.
- **RAG-assisted investigation:** retrieve relevant code and evidence to help an LLM investigate possible causes.
- **Patch proposals:** generate focused diffs and validate that they apply cleanly.
- **Sandbox testing:** run available tests in an isolated environment before describing a patch as verified.

## Core Principles

- **Multi-signal evidence:** candidate locations should be supported by signals such as `stack_frame`, `ui_label`, `semantic`, `lexical`, `git_recent`, or `graph`.
- **Relative rank scores:** scores from a ranking system are relative ranking indicators, not calibrated probabilities.
- **Honest verification:** distinguish between verified, unverified, and failed patches based on actual test execution results.
- **Visual fallback:** if a screenshot is blank or irrelevant, reduce reliance on visual evidence and use logs and code-search signals instead.
- **Human review:** generated patches should be inspected before they are merged into a production codebase.

## System Architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                       Next.js Frontend                           │
│       Landing · New Analysis · Analysis Detail · Repos · History  │
└─────────────────────────────┬────────────────────────────────────┘
                              │ REST / SSE
┌─────────────────────────────▼────────────────────────────────────┐
│                        FastAPI Backend                            │
│             Repositories · Reports · Analyses · Patches           │
└────────────────┬─────────────────────────────┬───────────────────┘
                 │                             │
┌────────────────▼────────────┐   ┌────────────▼──────────────────┐
│ Task Runner / Orchestrator  │   │ Data & Storage                │
│ Background / async tasks    │   │ SQL · Vector store · Blob data│
└────────────────┬────────────┘   └───────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────────────────┐
│                    Analysis Pipeline                              │
│ 1. Input ingestion and validation                                  │
│ 2. Screenshot/video keyframe understanding                        │
│ 3. Error and stack-trace parsing                                   │
│ 4. Repository indexing and AST-aware chunking                      │
│ 5. Hybrid retrieval: dense + lexical + structural signals          │
│ 6. Evidence fusion and suspect ranking                             │
│ 7. RAG-assisted hypothesis investigation                           │
│ 8. Patch generation and diff validation                            │
│ 9. Sandboxed test execution and verification status                │
└───────────────────────────────────────────────────────────────────┘
```

### Fusion ranking

A ranking implementation can combine normalized evidence signals, for example:

\[
S = w_d R_d + w_l R_l + w_s H_s + w_u H_u + w_g C_g + w_p P_g
\]

Where dense and lexical retrieval ranks, stack-frame hits, UI-label hits, recent code changes, and graph proximity contribute to a combined score. Weights should be tuned and evaluated on a representative labelled dataset. The resulting score is a ranking score, not a probability.

## Analysis Pipeline

1. **Ingest:** validate uploaded artifacts and extract video keyframes when applicable.
2. **Visual understanding:** identify relevant UI elements, labels, and visible anomalies using OCR or a vision-language model.
3. **Log analysis:** parse errors and stack traces.
4. **Repository indexing:** extract symbols and code chunks; prepare lexical and vector indexes.
5. **Hybrid retrieval:** retrieve candidates using semantic similarity, BM25, stack frames, UI labels, and repository signals.
6. **Fusion ranking:** combine evidence to prioritize likely files and functions.
7. **Agentic investigation:** use a bounded RAG tool loop to inspect retrieved evidence and test hypotheses.
8. **Patch generation:** propose a minimal unified diff and validate it before application.
9. **Sandbox verification:** run configured tests in an isolated environment and report the actual result.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | Next.js App Router, TypeScript, Tailwind CSS |
| UI / data state | Framer Motion, TanStack Query, Zustand (where configured) |
| Code inspection | Monaco Editor and unified diff viewer (where configured) |
| Backend | Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLAlchemy |
| Task execution | Background tasks; Celery and Redis if configured |
| Database | PostgreSQL or SQLite, depending on configuration |
| Retrieval | BM25 lexical search, vector embeddings, hybrid ranking |
| Vector storage | Qdrant when configured; local fallback if implemented |
| Model providers | Configurable mock or external LLM/VLM providers, depending on environment |
| Verification | Docker-based sandboxing when configured |

Actual integrations depend on the environment variables and services enabled in the current checkout. Check `.env.example` and the project configuration before starting optional services.

## Quickstart

### Prerequisites

- Git
- Python 3.11 or newer
- Node.js and npm
- Optional: Docker Desktop for containerized services

### 1. Clone the repository

```bash
git clone https://github.com/Sakshi2909-web/sightfix-ai.git
cd sightfix-ai
```

### 2. Configure the environment

Review `.env.example` and create a local `.env` if required by the application. Add API keys only to your local environment; **never commit secrets to GitHub**.

### 3. Start the backend

```bash
cd backend
python -m venv .venv
```

On Windows:

```powershell
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies according to the backend's project configuration. If the project supports editable installation:

```bash
pip install -e .
```

If the repository provides seed data, run the documented seed command. Then start the API using the entry point configured in the backend:

```bash
uvicorn app.main:app --reload --port 8000
```

If that module path differs in the current checkout, check the backend README or application entry point.

### 4. Start the frontend

Open a second terminal from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser. The backend API may be available at `http://localhost:8000`, with interactive API documentation at `http://localhost:8000/docs` if enabled.

## Docker Compose

If the repository's Docker Compose configuration and environment variables are complete, you can start the configured services with:

```bash
docker compose up --build
```

Review `docker-compose.yml` and `.env.example` first. Service names, ports, and optional dependencies depend on the current configuration.

## Demo Workflow

A typical demonstration can follow these steps:

1. Open the SightFix AI frontend.
2. Submit a bug report with a screenshot or relevant UI capture.
3. Add the runtime error or stack trace.
4. Select or index the repository to investigate.
5. Review ranked suspect files/functions and the evidence behind them.
6. Inspect the generated patch diff.
7. Run the available tests in the configured sandbox.
8. Review the final status and test output before accepting a patch.

For a reliable demo, use a reproducible sample bug and confirm that the current test suite behaves as expected before presenting results.

## Evaluation

Evaluate the system on labelled bug reports and report measured results from the current implementation. Useful metrics include:

- **Acc@1 / Acc@3:** whether the correct file appears among the top one or three candidates.
- **MRR (Mean Reciprocal Rank):** rewards ranking the correct location higher.
- **Function-level hit rate:** whether the faulty function is identified.
- **Patch apply rate:** the fraction of generated patches that apply cleanly.
- **Test pass rate:** the fraction of patched cases whose configured tests pass.
- **Latency and cost:** end-to-end analysis time and model/API usage.

Run the repository's evaluation script if one is provided, for example:

```bash
python backend/eval/run_eval.py
```

Only publish numerical benchmark results after running the evaluation and confirming the dataset, sample count, and results. Do not treat placeholder or mock-demo scores as evidence of real-world performance.

## Security Considerations

- **Secrets:** redact API keys, tokens, passwords, and other sensitive values from logs and prompts.
- **Untrusted repositories:** treat source archives and repository content as untrusted input.
- **Path traversal:** validate archive paths and prevent files from escaping the extraction directory.
- **Sandboxing:** run tests and generated code with least privilege, resource limits, timeouts, and network access disabled where feasible.
- **Patch review:** inspect all generated changes before merging.
- **Data privacy:** avoid uploading private source code or screenshots to third-party model providers unless authorized.
- **Production readiness:** a Docker container alone is not a complete security boundary. Consider stronger isolation for high-risk workloads.

## Roadmap

- [ ] GitHub App integration for pull requests with evidence and test logs
- [ ] Browser-based bug reproduction and before/after visual comparison
- [ ] Mobile UI hierarchy ingestion
- [ ] Ranker evaluation and fine-tuning on labelled developer feedback
- [ ] Team workspaces, access control, and audit logs
- [ ] Expanded benchmark suite across languages and bug categories

## Contributing

Contributions and feedback are welcome. For substantial changes, open an issue first to discuss the proposed improvement. Add or update tests when changing behavior.

## License

Add the appropriate license file and update this section before distributing the project publicly.
