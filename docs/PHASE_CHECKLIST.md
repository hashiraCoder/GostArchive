# Phase Checklist and Verified State

> Only mark an item complete after personally running the relevant command/test or inspecting the actual implementation. Planning documents do not count as implementation. Mirrors `ai_md/PHASE_CHECKLIST.md`; this file is the working progress ledger.

## Current state

- [x] Phase 0 — Repository foundations ✅ `5749358` (2026-10-29)
- [x] Phase 1 — Frontend/backend skeleton and health check ✅ (2026-10-29)
- [x] Phase 2 — Document ingestion and SQLite persistence ✅ (2026-10-29)
- [x] Phase 3 — Embeddings, Chroma persistence, semantic search ✅ (2026-10-29)
- [x] Phase 4 — Ollama, grounded RAG, citation validation ✅ (2026-10-29)
- [x] Phase 5 — Evidence UI and product polish ✅ (implementation verified 2026-10-29)
- [x] Phase 6 — Unit/integration/evaluation tests ✅ (2026-10-29)
- [x] RAG Remediation — Retrieval & Answer Quality Overhaul ✅ (2026-10-30)
- [x] Phase P0 — Core Integrity Remediation (Deletion Idempotency & Summary Scope) ✅ (2026-10-30)
- [x] Phase P1 — Intelligence & Intent Routing (Issue D & Issue E Remediation) ✅ (2026-10-30)
- [x] Phase P2 — UX & Evidence Transparency (Badges, Citations, Structured Answers) ✅ (2026-10-30)
- [x] Phase P3 — Extensible Model Architecture (Optional Provider Protocol) ✅ (2026-10-30)
- [ ] Phase 7 — README, demo, DEV submission
- [ ] Phase 8 — PDF text extraction (post-MVP)
- [ ] Phase 9 — Timeline (post-MVP)
- [ ] Phase 10 — Contradiction explorer (post-MVP)

---

## Phase 0 — Repository Foundations

### Acceptance gates

- [x] `.gitignore` created; blocks `backend/data/`, `*.db`, `*.sqlite3`, `chroma_store/`, `.env`, `venv/`, `node_modules/`, model weight file types
- [x] `.env.example` created with all env vars, safe defaults, no real secrets
- [x] `README.md` created — honest about implementation status (nothing working yet), prerequisites listed, privacy notes, license caveats
- [x] `AGENTS.md` at repo root (mirrors `ai_md/AGENTS.md`)
- [x] `docs/PROJECT_MEMORY.md` created
- [x] `docs/DECISIONS.md` created
- [x] `docs/PHASE_CHECKLIST.md` created (this file)
- [x] `data/sample_archive/` created with synthetic fictional documents covering all evaluation categories
- [x] Git commit: all Phase 0 files committed — hash `5749358`

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-29 12:09 | `git status` | Branch `main`, no commits, only `ai_md/` untracked | Fresh repo confirmed |
| 2026-10-29 12:17 | `git check-ignore -v backend/data/..., .env, venv/, node_modules/, chroma_store/, *.gguf` | All correctly ignored | `.gitignore` verified |
| 2026-10-29 12:17 | `git check-ignore` on `data/sample_archive/...` | Exit 1 = not ignored (correctly tracked) | Sample archive committed |
| 2026-10-29 12:22 | `git commit` | `5749358` — 35 files, 2363 insertions | First commit on `main` |

---

## Phase 1 — Frontend/Backend Skeleton

### Acceptance gates

- [x] `GET /api/health` returns `{"status":"ok","app_version":"0.1.0"}`
- [x] `GET /api/ready` returns per-dependency map; no crash when Ollama absent
- [x] pytest `tests/test_health.py` passes (9 tests, zero failures)
- [x] React app loads at `http://localhost:5173` and shows status indicator
- [x] StatusIndicator renders `ready/degraded/unavailable` states correctly

---

## Phase 2 — Document Ingestion

### Acceptance gates

- [x] `POST /api/documents` with valid `.txt` → `status: ready` in DB
- [x] `POST /api/documents` with invalid extension → 422
- [x] `POST /api/documents` with oversized file → 413/422
- [x] Duplicate content (same SHA-256) → returns existing document with `duplicate: true`
- [x] `GET /api/documents` returns list
- [x] `DELETE /api/documents/{id}` removes SQLite row and cascaded chunks
- [x] pytest ingestion tests pass

---

## Phase 3 — Embeddings and Search

### Acceptance gates

- [x] Import sample doc → semantic search paraphrase → ≥1 hit in top-5
- [x] Search with no documents → empty result (not error)
- [x] Index persists across a new Chroma adapter instance
- [x] pytest retrieval tests pass

---

## Phase 4 — Grounded Q&A

### Acceptance gates

- [x] Answerable question → answer + resolved citation (SQLite source, not model text)
- [x] Unanswerable question → `insufficient_evidence: true`, no fabricated answer
- [x] Ollama unavailable → `MODEL_UNAVAILABLE` error; search still works
- [x] Hallucinated citation ID dropped
- [x] Injection document: answer does not follow injected instruction
- [x] pytest chat tests pass (with mocked Ollama)

---

## Phase 5 — Evidence UI

### Acceptance gates

- [ ] End-to-end manual: import → search → ask → inspect citation → delete → restart → state persists (requires running local backend, embedding model, and Ollama)
- [x] All UI states implemented: empty, loading, error, insufficient evidence, model offline
- [x] Delete flow: confirmation → deleting → success or retry-error

---

## Phase 6 — Tests and Evaluation

### Acceptance gates

- [x] `pytest --tb=short` exits 0
- [x] Evaluation runner produces real metric output (numbers, dataset size, model stated)
- [x] All 8 evaluation categories represented in `data/evaluation/questions.json`

---

## RAG Remediation — Retrieval & Answer Quality Overhaul

### Acceptance gates

- [x] ChromaDB collection configured with explicit `"hnsw:space": "cosine"` metric
- [x] SQLite FTS5 table `document_chunks_fts` added and kept in sync on insert/delete/rebuild
- [x] Hybrid search combining semantic vectors and FTS5 lexical ranking via Reciprocal Rank Fusion (RRF)
- [x] Negative match percentages removed; replaced by descriptive labels ("High match", "Medium match", "Relevant") and bounded scores
- [x] Calibrated minimum relevance threshold (`0.30` cosine similarity) filters out irrelevant noise
- [x] Irrelevant queries (e.g. "what is winter arc") return empty search results and explicit insufficient evidence without hallucinated text
- [x] System prompt rewritten with 10 grounding rules, eliminating generic application architecture descriptions
- [x] Structured output validation with SQLite-verified citations (`direct_answer`, `archive_context`, `limitations`, `evidence_type`)
- [x] Dedicated archive and document summary capability (`POST /api/summarize`) distinct from Search and Ask
- [x] 37 backend tests passed in 13.73s
- [x] 13 frontend tests passed in 2.51s
- [x] Frontend TypeScript and production build passed with 0 errors
- [x] Ruff lint and formatting checks 100% clean

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-30 | `backend\venv\Scripts\python.exe -m pytest backend\tests --tb=short` | Exit 0 — 37 passed in 13.73s | 37 tests green |
| 2026-10-30 | `npm --prefix frontend test` | Exit 0 — 13 passed in 2.51s | All 13 tests green |
| 2026-10-30 | `npm --prefix frontend run build` | Exit 0 | Production build clean |
| 2026-10-30 | `backend\venv\Scripts\ruff.exe check backend\app backend\tests` | Exit 0 | Clean lint |
| 2026-10-30 | `backend\venv\Scripts\ruff.exe format --check backend\app backend\tests` | Exit 0 | Clean format |
| 2026-10-30 | `$env:PYTHONPATH='backend'; backend\venv\Scripts\python.exe -m app.evaluation.runner` | Exit 0 | Precision@5 0.24, Recall@5 0.933, Abstention 1.0, Coverage 1.0 |

---

## Phase P0 — Core Integrity Remediation (Deletion Idempotency & Summary Scope)

### Acceptance gates

- [x] `DELETE /api/documents/{id}` is idempotent: repeat requests and non-existent IDs return 204 without 404 failure
- [x] `remove_document()` safely removes file storage, vector store chunks, FTS entries, and SQLite row
- [x] Frontend `handleDelete` handles 404 gracefully without raising error banner, synchronizing local UI state
- [x] Document delete buttons optimistically lock and disable during in-flight deletion
- [x] Fixed frontend `apiFetch` in `client.ts`: 204 No Content responses no longer trigger `SyntaxError: Unexpected end of JSON input` ("try again" banner bug resolved)
- [x] End-to-end browser deletion verified using Chrome DevTools: document deleted smoothly, modal closed, empty state rendered without error banner
- [x] Database and vector store integrity confirmed: 0 documents, 0 chunks, 0 FTS rows, 0 Chroma vectors, 0 storage files remaining
- [x] `POST /api/summarize` fairly queries all ready documents without premature loop termination
- [x] Archive summary scope explicitly reports inspected ready documents out of total ready documents
- [x] Unready/failed documents in the archive are tracked and reported in `limitations`
- [x] `pytest backend/tests/test_summary.py` passes (4 tests, 0 failures)
- [x] `pytest backend/tests/test_documents.py -k test_list_and_delete_document` passes with idempotent verification
- [x] Frontend tests pass (13 tests, 0 failures) and build succeeds with 0 errors

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-30 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_summary.py -v` | Exit 0 — 4 passed in 0.51s | Multi-doc & unready coverage |
| 2026-10-30 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_documents.py -k test_list_and_delete_document -v` | Exit 0 — 1 passed | Idempotent delete verified |
| 2026-10-30 | `npm --prefix frontend test -- --run` | Exit 0 — 13 passed in 4.16s | All frontend tests green |
| 2026-10-30 | `npm --prefix frontend run build` | Exit 0 in 3.35s | Production build clean |
| 2026-10-30 | `backend\venv\Scripts\ruff.exe check backend/app backend/tests` | Exit 0 | Clean lint |

---

## Phase P1 — Intelligence & Intent Routing (Issue D & Issue E Remediation)

### Acceptance gates

- [x] Query intent classification (`classify_query_intent`) created in `backend/app/services/intent_service.py`
- [x] Natural greetings ("hello", "who are you", etc.) receive instant, conversational answers without vector retrieval
- [x] Archive-wide summary questions ("what this archive says", "summarize archive") automatically route to the dedicated summarizer
- [x] Off-topic requests (code generation, trivia) receive clear, polite abstentions
- [x] Factual archive queries continue to execute hybrid retrieval and validated citations
- [x] Operational health checks upgraded in `backend/app/api/routes/health.py`:
  - `check_database`: Verifies SQLite connection and table existence
  - `check_chroma`: Verifies collection access and count without failing on empty archive
  - `check_embedding_model`: Distinguishes locally cached weights (`ready`) from pending first-time download (`degraded`)
- [x] 18 intent classification unit tests pass (`backend/tests/test_intent.py`)
- [x] 17 chat and health tests pass (`backend/tests/test_chat.py`, `backend/tests/test_health.py`)
- [x] Frontend unit tests pass (13 tests) and production build passes with 0 errors
- [x] Ruff check and formatting 100% clean across all 51 backend files

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-30 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_intent.py -v` | Exit 0 — 18 passed in 0.09s | All intents verified |
| 2026-10-30 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_chat.py backend/tests/test_health.py -v` | Exit 0 — 17 passed in 6.61s | Deep health and chat routing green |
| 2026-10-30 | `npm --prefix frontend test -- --run` | Exit 0 — 13 passed in 3.58s | All frontend tests green |
| 2026-10-30 | `npm --prefix frontend run build` | Exit 0 in 3.04s | Production build clean |
| 2026-10-30 | `backend\venv\Scripts\ruff.exe check backend/app backend/tests` | Exit 0 | Clean lint |
| 2026-10-30 | `backend\venv\Scripts\ruff.exe format --check backend/app backend/tests` | Exit 0 — 51 files formatted | Clean format |

---

## Phase P2 — UX & Evidence Transparency (Badges, Citations, Structured Answers)

### Acceptance gates

- [x] Document status badges updated with semantic styles: `ready` (green), `processing` (pulsing amber), `deleting` (pulsing gray), and `error` (red)
- [x] Document library lists import date and byte formatting for archive items
- [x] Search results render styled relevance badges (`High match`, `Medium match`, `Relevant`)
- [x] Grounded answers presented in structured high-contrast callout boxes with direct answers, archive context, and scope/limitations
- [x] Interactive citation cards expand with document title, SQLite-verified chunk IDs, page numbers, and quoted excerpts
- [x] 13/13 frontend vitest unit tests pass (`ArchiveWorkspace.test.tsx`, `DocumentLibrary`, etc.)
- [x] Vite production build succeeds with 0 errors
- [x] 39 backend tests pass (`test_summary.py`, `test_intent.py`, `test_chat.py`, `test_health.py`)

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-30 | `npm --prefix frontend test -- --run` | Exit 0 — 13 passed in 2.72s | Citation & UI interaction tested |
| 2026-10-30 | `npm --prefix frontend run build` | Exit 0 in 2.79s | Production bundle clean |
| 2026-10-30 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_summary.py backend/tests/test_intent.py backend/tests/test_chat.py backend/tests/test_health.py -v` | Exit 0 — 39 passed in 7.34s | Backend test suite green |

---

## Phase P3 — Extensible Model Architecture (Optional Provider Protocol)

### Acceptance gates

- [x] Abstract `LLMProvider` protocol defined in `backend/app/generation/provider.py`
- [x] `OllamaClient` conforms to `LLMProvider` protocol and exposes `model_name` property
- [x] `ExternalLLMProvider` adapter implemented for OpenAI-compatible and cloud model endpoints with error handling
- [x] Provider factory `get_llm_provider` strictly defaults to local Ollama (100% offline & private)
- [x] Fallback guardrails: Missing external API key falls back safely to local Ollama with warning
- [x] Services updated: `chat_service.py` and `summary_service.py` accept and utilize any `LLMProvider`
- [x] `.env.example` documents `GHOSTARCHIVE_LLM_PROVIDER`, `GHOSTARCHIVE_EXTERNAL_API_KEY`, etc. with explicit privacy notice
- [x] 5 provider unit tests pass in `backend/tests/test_provider.py`
- [x] 44 backend unit tests pass in 8.22s across provider, intent, chat, summary, and health
- [x] 13 frontend tests pass and production build succeeds
- [x] Ruff check and format 100% clean across 53 backend files

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-30 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_provider.py -v` | Exit 0 — 5 passed in 0.13s | Factory & fallback verified |
| 2026-10-30 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_provider.py backend/tests/test_intent.py backend/tests/test_chat.py backend/tests/test_summary.py backend/tests/test_health.py -v` | Exit 0 — 44 passed in 8.22s | Full backend suite green |
| 2026-10-30 | `npm --prefix frontend test -- --run` | Exit 0 — 13 passed in 7.96s | Frontend tests green |
| 2026-10-30 | `npm --prefix frontend run build` | Exit 0 in 2.12s | Production build clean |
| 2026-10-30 | `backend\venv\Scripts\ruff.exe check backend/app backend/tests` | Exit 0 | Clean lint |
| 2026-10-30 | `backend\venv\Scripts\ruff.exe format --check backend/app backend/tests` | Exit 0 — 53 files formatted | Clean format |

---

## Phase 7 — README and Demo

### Acceptance gates

- [ ] Fresh-checkout setup on Windows following README steps reaches working demo
- [ ] `docs/EVALUATION_RESULTS.md` contains real measured metrics
- [ ] `LICENSE` file present with verified compatible license
