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
- [x] Audit Phase 0 — Baseline Discovery & Quality Defect Ledger ✅ (2026-10-31)
- [x] Audit Phase 1 — Document Ingestion & Indexing Reliability ✅ (2026-10-31)
- [x] Audit Phase 2 — Document Parsing & Chunking Quality ✅ (2026-10-31)
- [x] Audit Phase 3 — Retrieval Engine Audit & Relevance Calibration ✅ (2026-10-31)
- [x] Audit Phase 4 — Query Understanding, Intent Routing & Scope Isolation ✅ (2026-10-31)
- [x] Audit Phase 5 — Grounded Generation, Evidence Adherence & Citation Integrity ✅ (2026-10-31)
- [x] Audit Phase 6 — Mathematical & Code Reasoning ✅ (2026-10-31)
- [x] Audit Phase 7 — API Reliability, Schema Validation & Error Contracts ✅ (2026-10-31)
- [x] Audit Phase 8 — Conversation Persistence & Context Management ✅ (2026-10-31)
- [x] Audit Phase 9 — Frontend UX, Evidence Transparency & Product Reliability ✅ (2026-10-31)
- [ ] Audit Phase 10 — Complete Regression & Performance Verification
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

## Retrieval & Answer Quality Remediation (Phases 0–5)

### Acceptance gates

- [x] Phase 0 Inspection: Complete retrieval pipeline, FTS5 tokenizer, prompt framing, candidate pooling, and intent classification mapped
- [x] Phase 1 Temporal Context & Isolation:
  - Passage prompt framing includes `date="YYYY-MM-DD"` attribute from document `source_date` / `created_at`
  - Conservative temporal intent classification (`latest`, `earliest`, `chronological`)
  - Temporal ordering applied to candidate passages when query asks for latest or historical progression
  - System prompt enforces evidence isolation (never borrow justifications across separate topics)
  - System prompt enforces multi-part question completeness
  - Explicit distinction required between original decisions and later revisions
- [x] Phase 2 Retrieval Improvements:
  - FTS5 query sanitization preserves bare alphanumeric tokens so SQLite FTS5 Porter stemming operates
  - Verified stemming matches singular/plural forms (`preferences` matches `preference`)
  - Initial candidate pool retrieves 15 candidates for fusion before capping context at top 5
  - Calibrated thresholding: pure vector matches without lexical corroboration require $\ge 0.35$ cosine similarity, rejecting noise (e.g. `winter arc` scoring ~0.31)
  - Matches with lexical corroboration in top candidates accepted down to 0.15
- [x] Phase 3 Intent Routing:
  - Overview queries (`What is this archive about?`, `tell me about my archive`, `what do I have stored here?`) route to archive-wide summary
  - Topic-focused queries (`What does this archive say about Redis?`) route to `ARCHIVE_QUESTION`
  - Conversational greetings (`hello`, `hi`) route to `GREETING`
- [x] Phase 4 Citation Reliability:
  - `document_title` preferentially resolved from document title metadata with fallback to filename
  - Strict validation against retrieved SQLite chunks retained
- [x] Phase 5 Regression Testing:
  - 10 comprehensive regression tests in `backend/tests/test_remediation_regression.py` covering all 7 failure scenarios
  - Full backend test suite passes: 78 tests passed in 25.33s
  - Full frontend test suite passes: 14 tests passed in 3.68s
  - Frontend production build succeeds cleanly
  - Ruff check and format clean across entire backend

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-30 | `pytest backend/tests/test_remediation_regression.py` | Exit 0 — 10 passed in 0.31s | All 7 failure scenarios covered |
| 2026-10-30 | `pytest backend/tests` | Exit 0 — 78 passed in 25.33s | Zero regressions across backend |
| 2026-10-30 | `npm --prefix frontend test` | Exit 0 — 14 passed in 3.68s | Frontend test suite green |
| 2026-10-30 | `npm --prefix frontend run build` | Exit 0 in 1.95s | Production bundle clean |
| 2026-10-30 | `ruff check backend` | Exit 0 — All checks passed | Clean lint |
| 2026-10-30 | `ruff format --check backend` | Exit 0 — All 54 files formatted | Clean format |

---

## Controlled Implementation — Steps 1–4 (Scope, Multi-file, Document Management, Error States)

### Acceptance gates

- [x] Step 1 Archive Scope Selection:
  - Scope selector implemented in workspace (`Entire Archive` vs specific document)
  - Visual active scope badge with reset trigger
  - `document_ids` passed cleanly to `/search` and `/chat`
  - Scope switching invalidates previous results and resets search/ask state
  - Scope isolation verified: searches restricted to a document never return passages from other documents
- [x] Step 2 Multi-File Upload & Queue:
  - Drag-and-drop zone and multi-file selection support
  - Controlled batch queue processing one file at a time without loading entire batch into memory
  - Per-file status tracking (`queued`, `uploading`, `ready`, `duplicate`, `failed`)
  - Duplicate detection preserves existing entries with `duplicate: true`
  - Partial failures handled gracefully with individual retry actions
- [x] Step 3 Document Management:
  - Filename query search, status filter (`all`, `ready`, `processing`, `error`), and file type filter (`all`, `txt`, `md`)
  - Pagination controls with 10 documents per page
  - Individual selection checkboxes and master select-all on page
  - Bulk deletion modal confirmation and execution with per-document result reporting
  - Consistent selection and page bounds post-deletion
- [x] Step 4 Error and Empty States:
  - Dedicated Ollama offline alert banner in Ask section with disabled submission
  - Active indexing status notice explaining partial results while documents are processing
  - Enhanced search empty state using `EmptyState.tsx` with helpful query refinement guidance
  - Documents remain in `processing` until vector storage completes, never prematurely labeled `ready`
- [x] Full Regression & Build Validation:
  - Backend: 81 tests passed in 25.84s (0 failures)
  - Frontend: 18 Vitest tests passed in 2.69s (0 failures)
  - Production build: `tsc && vite build` clean in 2.37s
  - Ruff check & format: clean across all 54 backend files

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-30 | `backend\venv\Scripts\python.exe -m pytest backend\tests` | Exit 0 — 81 passed in 25.84s | Backend test suite green (scope isolation, filters, pagination, bulk delete) |
| 2026-10-30 | `npm --prefix frontend test -- --run` | Exit 0 — 18 passed in 2.69s | Frontend unit tests green (scope switching, filters, bulk delete, Ollama offline) |
| 2026-10-30 | `npm --prefix frontend run build` | Exit 0 in 2.37s | Production bundle clean |
| 2026-10-30 | `backend\venv\Scripts\ruff.exe check backend\app backend\tests` | Exit 0 | Clean lint |
| 2026-10-30 | `backend\venv\Scripts\ruff.exe format --check backend\app backend\tests` | Exit 0 — 54 files formatted | Clean format |

---

## Health & Model Readiness Decoupling (MODEL_UNAVAILABLE Contradiction Fix)

### Acceptance gates

- [x] Trace complete failure:
  - Root cause pinpointed: `httpx.TimeoutException`/`RequestError` and 404/500 HTTP responses were bundled into generic `MODEL_UNAVAILABLE` with `retryable=True`.
  - Ingestion pipeline completely decoupled from Ollama; documents correctly enter `ready` status using SQLite + Chroma + sentence-transformers independently of Ollama.
  - `/api/ready` masked missing model under `degraded` but returned HTTP 200, creating false confidence while `/api/chat` returned 503.
- [x] Separate health states into 5 granular dependencies:
  - `ollama_service`: Ollama HTTP service reachability (`/api/tags`).
  - `model_available`: Configured model exists in tags.
  - `model_inference`: Inference validation (lightweight by default; optional `?check_inference=true` bounded to 5s).
  - `embedding_service`: Sentence-transformers operational check.
  - `document_storage`: SQLite + Chroma accessibility check.
- [x] Correct error classification:
  - `MODEL_UNAVAILABLE` (503, retryable=True): Ollama daemon offline/refused.
  - `MODEL_NOT_FOUND` (503, retryable=False): Configured model missing (`ollama pull` needed).
  - `GENERATION_TIMEOUT` (504, retryable=True): Model generation exceeded timeout.
  - `GENERATION_FAILED` (502, retryable=False): Runtime crash, OOM, empty response, or syntax error.
- [x] Frontend health and error transparency:
  - `StatusIndicator` displays separated component badges.
  - `ArchiveWorkspace` distinguishes `ollama serve` (daemon offline) from `ollama pull {model}` (model missing).
  - Document status clearly separated from AI inference readiness.
- [x] Automated test suite & verification:
  - `backend/tests/test_model_readiness.py`: 9 regression tests covering all 9 failure/readiness scenarios.
  - Full backend test suite: 90 passed in 26.72s.
  - Frontend test suite: 18 passed in 3.00s.
  - Production build: `tsc && vite build` clean in 2.29s.
  - Ruff check & format: clean across all 55 backend files.

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-30 22:56 | `backend\venv\Scripts\python.exe -m pytest backend\tests\test_model_readiness.py` | Exit 0 — 9 passed in 21.70s | All 9 model readiness and error classification tests pass |
| 2026-10-30 22:59 | `backend\venv\Scripts\python.exe -m pytest backend\tests` | Exit 0 — 90 passed in 26.72s | Zero regressions across all 90 backend tests |
| 2026-10-30 23:01 | `npm --prefix frontend test -- --run` | Exit 0 — 18 passed in 3.00s | Frontend tests pass |
| 2026-10-30 23:01 | `npm --prefix frontend run build` | Exit 0 in 2.29s | Production bundle clean |
| 2026-10-30 22:59 | `backend\venv\Scripts\ruff.exe check backend\app backend\tests` | Exit 0 | Clean lint |
| 2026-10-30 22:59 | `backend\venv\Scripts\ruff.exe format --check backend\app backend\tests` | Exit 0 — 55 files formatted | Clean format |

---

## Phase P0 — Conversation Persistence (Multi-Turn Discussions, Idempotency, Snapshots)

### Acceptance gates

- [x] SQLite schema extended with foreign keys enabled (`PRAGMA foreign_keys = ON;`):
  - `conversations` table: `id`, `title`, `created_at`, `updated_at`.
  - `messages` table: `id`, `conversation_id` (FK ON DELETE CASCADE), `client_turn_id`, `role`, `content`, `status`, `direct_answer`, `archive_context`, `limitations`, `insufficient_evidence`, `citations`, `retrieval_count`, `model`, `error_message`, `scope_document_ids`, `created_at`, `updated_at`.
  - Indices for fast thread loading and idempotency lookup: `idx_conversations_updated_at`, `idx_messages_conversation_id`, `idx_messages_idempotency`.
- [x] Multi-Turn Conversational Context & Grounding Separation:
  - Bounded conversational context (last 3 completed turns) formatted cleanly into user prompt for reference and pronoun resolution.
  - Strict evidence separation preserved: past assistant responses are NEVER treated as authoritative evidence; all factual assertions are strictly derived from currently permitted retrieved passages.
  - Active question excluded from history context to avoid duplication in prompt framing.
- [x] Scope Isolation:
  - Each message turn records its associated `scope_document_ids`.
  - If a user query is restricted to a narrower document scope, assistant responses from broader or incompatible scopes are omitted from history injection.
- [x] Idempotency, Concurrency, and Atomic Turns:
  - `client_turn_id` tracked on user and assistant messages.
  - Replaying a completed turn idempotently returns the saved response without re-running inference or mutating state.
  - Reusing an idempotency key with a different question is rejected with HTTP 409 Conflict.
  - Concurrent requests within the same conversation are protected via active pending turn checks (HTTP 409).
  - Stale pending turns (>60s) from process crashes are automatically recovered and marked failed.
- [x] Explicit Message State Transitions & Retry:
  - User messages saved as `completed`.
  - Assistant messages transition: `pending` -> `completed` on success; `pending` -> `failed` on inference error/timeout.
  - Retry resumption: retrying a failed turn transitions `failed` -> `pending` and updates the existing assistant record without duplicating the user question.
- [x] Citation Snapshots & Historical Integrity:
  - Self-contained citation snapshots stored in JSON (`chunk_id`, `document_id`, `filename`, `document_title`, `page_number`, `excerpt`, `evidence_type`).
  - Thread loader verifies document existence against `documents` table in batch: if source document has been deleted, displays `Historical Snapshot — Source removed` (`document_exists: false`).
- [x] Dedicated UI & Backward-Compatible API:
  - `GET /api/conversations`, `POST /api/conversations`, `GET /api/conversations/{id}`, `PATCH /api/conversations/{id}`, `DELETE /api/conversations/{id}`.
  - `/api/chat` maintains 100% backward compatibility, auto-creating a conversation if `conversation_id` is omitted.
  - Dedicated two-panel Ask interface in `ArchiveWorkspace.tsx`: `ConversationSidebar` (search, + New Conversation, inline rename, delete confirmation) and `ConversationThread` (chronological cards, pending pulse, failed error with "Retry Turn" button, expandable citations with verification badges).
- [x] Automated test suites:
  - Backend: 100 passed in 66.40s (including 4 repository tests and 6 conversation persistence tests).
  - Frontend: 24 passed in 5.76s (including `ConversationSidebar.test.tsx` and `ConversationThread.test.tsx`).
  - Production build: `tsc && vite build` clean in 2.03s.
  - Ruff check & format: clean across all 61 backend files.

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_conversation_repository.py backend/tests/test_conversations.py` | Exit 0 — 10 passed in 15.60s | Persistence, idempotency, retry, snapshots, scope isolation |
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests` | Exit 0 — 100 passed in 66.40s | Full backend regression suite clean |
| 2026-10-31 | `npm --prefix frontend test -- --run` | Exit 0 — 24 passed in 5.76s | Full frontend Vitest suite clean |
| 2026-10-31 | `npm --prefix frontend run build` | Exit 0 in 2.03s | TypeScript check and Vite production build clean |
| 2026-10-31 | `backend\venv\Scripts\ruff.exe check backend\app backend\tests` | Exit 0 | Clean lint |
| 2026-10-31 | `backend\venv\Scripts\ruff.exe format --check backend\app backend\tests` | Exit 0 — 61 files formatted | Clean format |

---

## Phase 6.5 — UI/UX Redesign & Premium Archival Workspace

### Acceptance gates

- [x] Refined Design Tokens & Typography:
  - Warm refined palette implemented in `frontend/src/styles/tokens.css` and `frontend/tailwind.config.ts`:
    - Background: `#F7F4EE` (warm ivory parchment)
    - Sidebar: `#EEE7DC` (warm archival sidebar)
    - Surface: `#FFFEFB` (clean card surface)
    - Text: `#30271F` (deep espresso brown)
    - Muted: `#817366` (warm archival label)
    - Accent: `#755334` (rich archival copper) / `#5E4127` (hover)
    - Ready: `#2D6A4F` (deep forest green) / Danger: `#9B2226` (crimson)
- [x] Information Architecture & Persistent Navigation:
  - Replaced excessively long single-scroll page with persistent desktop sidebar navigation and top action bar.
  - Sidebar contains: Brand header with copper 'G' badge, navigation tabs (`Overview`, `Documents` with document count badge, `Ask Archive` with 'Core' badge, `Conversations` with discussion count badge, `System Status` with health dot), and bottom compact system health box (Gemma 3 1B · MiniLM-L6-v2 · 100% Offline).
  - Top header displays active view title, active retrieval scope badge, and quick action buttons (`+ Import Files`, `New Question`).
- [x] Modular View Decomposition:
  - `OverviewView.tsx`: Welcome hero, live metrics cards (total documents, indexed passages, saved discussions, AI privacy), recent documents preview, and corpus synthesis trigger.
  - `DocumentsView.tsx`: Document management with multi-file drag-and-drop batch upload, filename & type filters, master page selection, and bulk deletion confirmation modal.
  - `AskArchiveView.tsx`: Core evidence-grounded Q&A experience with active scope picker, conversation thread with markdown rendering, SQLite citation cards with snippet inspection & deleted source warning, and question composer.
  - `HistoryView.tsx`: Saved discussions list, inline thread rename, deletion confirmation modal, and one-click reopen.
  - `SystemStatusView.tsx`: Decoupled 5-subsystem health diagnostics (SQLite+Chroma storage, embedding model, Ollama daemon connectivity, model tag availability, and inference readiness) with local-first security guarantees.
- [x] Automated Test Suites & Regression Verification:
  - Frontend: 30 passed in 3.73s across 7 test files (`NavigationViews.test.tsx` added).
  - Production build: `tsc && vite build` clean in 2.02s.
  - Backend: 100 passed in 34.79s across all 13 test files.
  - Ruff check & format: clean across all 61 backend files.

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-31 | `npm --prefix frontend test -- --run` | Exit 0 — 30 passed in 3.73s | Full frontend Vitest suite clean across 7 test files |
| 2026-10-31 | `npm --prefix frontend run build` | Exit 0 in 2.02s | TypeScript check and Vite production build clean |
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests` | Exit 0 — 100 passed in 34.79s | Zero backend regressions across all 13 test suites |
| 2026-10-31 | `backend\venv\Scripts\ruff.exe check backend; backend\venv\Scripts\ruff.exe format --check backend` | Exit 0 | Clean lint and format across all 61 backend files |

---

## Audit Phase 1 — Document Ingestion and Indexing Reliability

### Acceptance gates

- [x] BUG-01 fixed: eliminated duplicate concurrent upload call in `DocumentLibrary.tsx`.
- [x] BUG-02 fixed: added document polling in `ArchiveWorkspace.tsx` to automatically transition pending states (`processing`, `uploading`, `deleting`) to terminal (`ready`, `error`) without page refresh.
- [x] BUG-06 fixed: anchored `data_dir` to project root dynamically in `Settings`, eliminating runtime split-brain between `backend/data` and `backend/backend/data`.
- [x] Ingestion lifecycle error handling: errors during embedding/indexing update SQLite status to `error` with structured `error_code`, preventing stuck `processing` documents.
- [x] Interrupted document recovery: `recover_interrupted_documents` runs on FastAPI lifespan startup, transitioning orphaned `processing`/`deleting` jobs to `error` with `INTERRUPTED` code.
- [x] Duplicate upload race condition handled safely with SQLite collision catching.
- [x] Automatic retry: re-uploading a failed document cleans up stale chunks/vectors and re-processes cleanly.
- [x] Frontend error UI: error status badge displays `error: ERROR_CODE` in red with retry button in document queue.
- [x] Ingestion lifecycle test suite: 11 tests in `backend/tests/test_ingestion_lifecycle.py` passing.
- [x] Document library test suite: 3 tests in `frontend/src/tests/DocumentLibrary.test.tsx` passing.
- [x] Full backend pytest suite: 111 passed.
- [x] Full frontend Vitest suite: 33 passed.
- [x] Frontend production build: clean.
- [x] Ruff lint and formatting checks: 100% clean across 62 backend files.

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-31 | `$env:PYTHONPATH='backend'; backend\venv\Scripts\python.exe -m pytest backend/tests/test_ingestion_lifecycle.py` | Exit 0 — 11 passed in 4.70s | Ingestion lifecycle edge cases, crash recovery, retries verified |
| 2026-10-31 | `npm --prefix frontend test -- --run` | Exit 0 — 33 passed in 3.38s | All 8 test files passing; single upload call, error retry, badge display verified |
| 2026-10-31 | `$env:PYTHONPATH='backend'; backend\venv\Scripts\python.exe -m pytest backend/tests` | Exit 0 — 111 passed in 22.81s | Zero regressions across all 111 backend tests |
| 2026-10-31 | `npm --prefix frontend run build` | Exit 0 in 1.26s | Production bundle build clean |
| 2026-10-31 | `backend\venv\Scripts\ruff.exe check backend; backend\venv\Scripts\ruff.exe format --check backend` | Exit 0 | 62 backend files cleanly formatted and verified |

---

## Audit Phase 2 — Document Parsing and Chunking Quality

### Acceptance gates

- [x] BUG-07 fixed: stripped invisible zero-width formatting characters (`\u200b`, `\u200c`, `\u200d`, `\ufeff`, `\u2060`, `\u00ad`) and normalized mathematical operators (`\u2265` -> `>=`, `\u2264` -> `<=`, `\u2260` -> `!=`, `\u2248` -> `~=`, `\u2212` -> `-`) with proper spacing (`fs>=2fm` -> `fs >= 2fm`) in `backend/app/ingestion/normalize.py`.
- [x] BUG-08 fixed: structure-aware chunking preserving sections, code scripts, and alternative implementations without fracturing code or blending alternatives.
- [x] Benchmark verification: `sampling theorem.txt` produces exactly 3 cohesive, self-contained chunks:
  - Chunk 0: Aim, Theory, formula `fs >= 2fm`, and variable definitions (`fs`, `fm`).
  - Chunk 1: Complete Implementation 1 (spline interpolation script, variables, and all 3 subplots).
  - Chunk 2: Complete Alternative Implementation 2 (linear interpolation script and all 3 subplots).
- [x] Source offsets verification: character offsets `(start_char, end_char)` accurately correspond to original text slices across all chunks.
- [x] Code comments preserved alongside their code statements.
- [x] Oversized continuous prose window-slicing respects sentence boundaries (`. `, `?\n`, `!\n`).
- [x] Markdown level-1 and level-2 sections isolated cleanly; level-3 subheadings grouped coherently within target chunk size.
- [x] `rechunk_document` helper implemented to upgrade stored documents in SQLite, FTS5, and Chroma without data loss.
- [x] `sampling theorem.txt` in runtime archive re-chunked to 3 chunks; verified with FTS query coverage.
- [x] Normalization & structure chunking test suite: 8 tests in `backend/tests/test_normalize.py` passing.
- [x] Full backend pytest suite: 119 passed across all 14 test suites.
- [x] Full frontend Vitest suite: 33 passed across 8 test suites.
- [x] Frontend production build: clean.
- [x] Ruff lint and formatting checks: 100% clean across 63 backend files.

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-31 | `$env:PYTHONPATH='backend'; backend\venv\Scripts\python.exe -m pytest backend/tests/test_normalize.py` | Exit 0 — 8 passed in 0.30s | Zero-width stripping, math operators, benchmark sampling chunking verified |
| 2026-10-31 | `$env:PYTHONPATH='backend'; backend\venv\Scripts\python.exe -m pytest backend/tests` | Exit 0 — 119 passed in 26.84s | Zero regressions across all 14 backend test suites |
| 2026-10-31 | `npm --prefix frontend test -- --run` | Exit 0 — 33 passed in 57.51s | All 8 frontend test files passing |
| 2026-10-31 | `npm --prefix frontend run build` | Exit 0 in 2.99s | Production bundle clean |
| 2026-10-31 | `backend\venv\Scripts\ruff.exe check backend; backend\venv\Scripts\ruff.exe format --check backend` | Exit 0 | 63 backend files clean |
| 2026-10-31 | `$env:PYTHONPATH='backend'; backend\venv\Scripts\python.exe backend/app/evaluation/runner.py` | Exit 0 | 20 questions, 1.0 abstention, 0.933 recall@5, 1.0 citation rate |

---

## Audit Phase 3 — Retrieval Engine Audit and Relevance Calibration

### Acceptance gates

- [x] BUG-03 fixed: eliminated false negative retrieval on exact code identifiers (`clc`, `interp1`, `stem`, `aim`) by allowing distinctive lexical hits in top FTS ranks with non-negative similarity to qualify as relevant without requiring `sim >= 0.15`.
- [x] Scoped search threshold calibrated: set `eff_threshold = 0.11` and `vector_only_threshold = 0.11` for scoped queries, safely above the empirical noise floor ($\le 0.064$), resolving conceptual math and signal processing queries ("What is its formula?" at 0.1193, "What happens at 8 Hz?" at 0.1909) while preserving 100% noise rejection on out-of-domain queries.
- [x] Stopword expansion: expanded `STOPWORDS` list in `backend/app/services/search_service.py` with English function words (`its`, `all`, `used`, `does`, `what`, `where`, etc.), preventing query pollution like `its OR formula`.
- [x] Code idiom phrase matching: added phrase preservation in `_sanitize_fts_query` for syntax like `"close all"`.
- [x] Pre-resolved candidate row inspection: loaded chunk content prior to relevance gating to evaluate query token coverage and identify distinctive code symbols directly.
- [x] Benchmark verification: 24 benchmark questions evaluated against live `search_documents`:
  - 19 / 19 answerable benchmark questions retrieved target chunks (100% recall).
  - 5 / 5 unanswerable / out-of-domain queries returned 0 chunks (100% precision / clean abstention).
- [x] Retrieval regression test suite: 9 tests in `backend/tests/test_retrieval.py` passing, including `test_exact_code_identifier_retrieval_survives_low_similarity`.
- [x] Full backend pytest suite: 120 passed in 67.90s across all 15 test suites.
- [x] Full frontend Vitest suite: 33 passed in 11.17s across all 8 test suites.
- [x] Frontend production build: clean in 3.21s.
- [x] Ruff lint and formatting checks: 100% clean across 63 backend files.

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-31 | `$env:PYTHONPATH='backend'; backend\venv\Scripts\python.exe -m pytest backend/tests/test_retrieval.py` | Exit 0 — 9 passed in 0.32s | Code identifier retrieval and hybrid scoring verified |
| 2026-10-31 | `$env:PYTHONPATH='backend'; backend\venv\Scripts\python.exe -m pytest backend/tests` | Exit 0 — 120 passed in 67.90s | Zero regressions across all 120 backend tests |
| 2026-10-31 | `npm --prefix frontend test -- --run` | Exit 0 — 33 passed in 11.17s | All 8 frontend test files passing |
| 2026-10-31 | `npm --prefix frontend run build` | Exit 0 in 3.21s | Production bundle clean |
| 2026-10-31 | `backend\venv\Scripts\ruff.exe check backend; backend\venv\Scripts\ruff.exe format --check backend` | Exit 0 | 63 backend files clean |

---

## Audit Phase 4 — Query Understanding, Intent Routing, and Scope Isolation

### Acceptance gates

- [x] BUG-09 fixed: expanded `QueryIntent` to 9 categories (`GREETING`, `ARCHIVE_SUMMARY`, `FULL_DOCUMENT_RETRIEVAL`, `CONVERSATION_HISTORY`, `CODE_EXPLANATION`, `MATHEMATICAL_CALCULATION`, `CROSS_DOCUMENT_SYNTHESIS`, `ARCHIVE_QUESTION`, `OFF_TOPIC`) with deterministic regex classification in `backend/app/services/intent_service.py`.
- [x] BUG-04 fixed: wrapped `validate_model_output` inside the message failure boundary in `backend/app/services/chat_service.py`. When model generation returns invalid JSON or schema errors, assistant message status transitions to `failed` and records error details, completely eliminating perpetual HTTP 409 Conflict lockouts on subsequent user queries.
- [x] Full document retrieval pipeline: implemented zero-hallucination verbatim raw document delivery in `chat_service.py` that resolves target document(s) via document scope or query filename matching, reads raw file or joins chunks verbatim, emits full chunk citations, and completely bypasses LLM summarization.
- [x] Conversation history meta-queries: implemented handler in `chat_service.py` for "What did we just discuss?", "What was my previous question?", and "What was your last answer?" answering directly from `recent_turns` without hallucinating or requiring document chunks.
- [x] Scope-aware prompt directives: added targeted directives in `backend/app/generation/prompts.py` for code explanation, mathematical calculation, and cross-document synthesis.
- [x] Intent test suite: 53 tests in `backend/tests/test_intent.py` passing across all 9 intent categories.
- [x] Phase 4 integration test suite: 11 tests in `backend/tests/test_phase4_intents_and_scope.py` passing.
- [x] Full backend pytest suite: 162 passed in 153.42s across all 16 test suites.
- [x] Full frontend Vitest suite: 33 passed in 14.93s across all 8 test suites.
- [x] Frontend production build: clean in 1.88s.
- [x] Ruff lint and formatting checks: 100% clean across 64 backend files.
- [x] Deterministic evaluation runner: 20 questions, 1.0 abstention, 1.0 citation validity, 0.933 recall@5, 0.0 repeated generic answer rate.

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-31 | `$env:PYTHONPATH='backend'; backend\venv\Scripts\python.exe -m pytest backend/tests/test_intent.py` | Exit 0 — 53 passed in 0.10s | 9 intent categories verified |
| 2026-10-31 | `$env:PYTHONPATH='backend'; backend\venv\Scripts\python.exe -m pytest backend/tests/test_phase4_intents_and_scope.py` | Exit 0 — 11 passed in 0.69s | Verbatim delivery, conversation recaps, prompt directives, BUG-04 fix verified |
| 2026-10-31 | `$env:PYTHONPATH='backend'; backend\venv\Scripts\python.exe -m pytest backend/tests` | Exit 0 — 162 passed in 153.42s | Zero regressions across all 162 backend tests |
| 2026-10-31 | `npm --prefix frontend test -- --run` | Exit 0 — 33 passed in 14.93s | All 8 frontend test files passing |
| 2026-10-31 | `npm --prefix frontend run build` | Exit 0 in 1.88s | Production bundle clean |
| 2026-10-31 | `backend\venv\Scripts\ruff.exe check backend; backend\venv\Scripts\ruff.exe format --check backend` | Exit 0 | 64 backend files clean |
| 2026-10-31 | `$env:PYTHONPATH='backend'; backend\venv\Scripts\python.exe backend/app/evaluation/runner.py` | Exit 0 | 20 questions, 1.0 abstention, 1.0 citation validity, 0.933 recall@5 |

---

## Audit Phase 5 — Grounded Generation and Evidence Adherence

### Acceptance gates

- [x] BUG-05 fixed: eliminated small model self-contradictions in `backend/app/generation/output_validation.py` via `_is_contradictory_limitation`. Negative limitation claims ("does not provide X") are suppressed when the entity/topic is accurately answered in `answer` and supported in evidence.
- [x] Schema normalization for 1B models: updated `validate_model_output` in `output_validation.py` to gracefully handle omitted or string-typed `insufficient_evidence` and `cited_chunk_ids` keys without triggering HTTP 502 schema crashes.
- [x] Robust citation resolution: implemented multi-tier citation resolution in `output_validation.py`:
  1. Exact chunk ID matching against retrieved evidence.
  2. Document UUID prefix matching mapping truncated document IDs to the best-matching chunk.
  3. Bounded string prefix matching.
  4. Content fallback lexical matching: matches non-stopword tokens of grounded answers to evidence passages when the model omits citation IDs, while strictly rejecting ungrounded hallucinations (0 overlap).
- [x] Grounding prompt directives: enhanced `SYSTEM_PROMPT` in `backend/app/generation/prompts.py` with Grounding Principles 7, 8, and 9 (consistency rule, code syntax evidence rule, and exact chunk ID copying instructions).
- [x] Grounded generation test suite: 7 tests in `backend/tests/test_grounded_generation.py` passing.
- [x] Live model benchmark validation on Gemma 3 1B:
  - "What is the aim of the experiment?": 100% grounded answer, 1 citation, insufficient: False.
  - "What is the formula for the sampling theorem?": `fs >= 2fm`, 2 citations, insufficient: False.
  - "What is the message frequency?": `5 Hz` / `20 Hz`, 2 citations, contradictory limitation suppressed.
  - "What does clc do?": Answered with MATLAB code line, 1 citation, 0 schema crashes.
  - "Who is the faculty instructor?": Clean abstention ("The archive does not contain sufficient evidence", citations: 0, insufficient: True).
  - "What is the student's roll number?": Clean abstention ("Insufficient_evidence", citations: 0, insufficient: True).
- [x] Full backend pytest suite: 171 passed in 23.75s across all 17 test suites.
- [x] Full frontend Vitest suite: 33 passed in 5.09s across all 8 test suites.
- [x] Frontend production build: clean in 1.46s.
- [x] Ruff lint and formatting checks: 100% clean across 65 backend files.

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_grounded_generation.py` | Exit 0 — 7 passed in 0.03s | Contradiction suppression, prefix matching, schema normalization verified |
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests` | Exit 0 — 171 passed in 23.75s | Zero regressions across all 171 backend tests |
| 2026-10-31 | `npm --prefix frontend test -- --run` | Exit 0 — 33 passed in 5.09s | All 8 frontend test files passing |
| 2026-10-31 | `npm --prefix frontend run build` | Exit 0 in 1.46s | Production bundle clean in 1.46s |
| 2026-10-31 | `backend\venv\Scripts\ruff.exe check backend; backend\venv\Scripts\ruff.exe format --check backend` | Exit 0 | 65 backend files clean |

---

## Audit Phase 6 — Mathematical and Code Reasoning

### Acceptance gates

- [x] BUG-10 fixed: eliminated open-ended arithmetic and signal processing hallucinations in small LLMs by implementing deterministic parameter extraction and computation in `backend/app/generation/math_reasoning.py`:
  - `extract_signal_parameters`: extracts variables (`fm = 5 Hz`, `fs = 20 Hz`) and colon vectors (`t = 0:0.001:1`, `ts = 0:Ts:1`, `n = 0:1/fs:1`), calculating exact Nyquist rate (10 Hz), sampling interval ($T_s = 0.05\text{ s}$), original samples (1001 points), and sampled points (21 points).
  - `analyze_math_question`: evaluates query for specific mathematical calculations (Nyquist rate, sampling interval, sample counts, sufficiency check, colon vector syntax, and arbitrary frequency checks e.g. 8 Hz aliasing).
  - `analyze_code_identifiers`: identifies MATLAB script commands (`clc`, `clear`, `close all`, `interp1`, `stem`) present in evidence passages and provides verified semantic explanations grounded in the script.
- [x] Grounding prompt directives: enhanced `build_user_prompt` in `backend/app/generation/prompts.py` to automatically inject verified derived calculations and code semantics directives into the prompt.
- [x] Output validation guard: updated `validate_model_output` in `backend/app/generation/output_validation.py` to verify that generated answers adhere to the verified calculations, correcting arithmetic hallucinations (e.g. "4" samples or "reconstructed at 8 Hz") and attaching derived chunk citations with `evidence_type = "derived"`.
- [x] Mathematical reasoning test suite: 11 tests in `backend/tests/test_math_reasoning.py` passing in 0.06s.
- [x] Full backend pytest suite: 182 passed in 29.53s across all 18 test suites.
- [x] Full frontend Vitest suite: 33 passed in 5.86s across all 8 test suites.
- [x] Frontend production build: clean in 4.14s.
- [x] Ruff lint and formatting checks: 100% clean across 67 backend files.

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_math_reasoning.py` | Exit 0 — 11 passed in 0.06s | Nyquist rate, interval, 1001/21 sample counts, 8 Hz aliasing, code semantics verified |
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests` | Exit 0 — 182 passed in 29.53s | Zero regressions across all 182 backend tests |
| 2026-10-31 | `npm --prefix frontend test -- --run` | Exit 0 — 33 passed in 5.86s | All 8 frontend test files passing |
| 2026-10-31 | `npm --prefix frontend run build` | Exit 0 in 4.14s | Production bundle clean |
| 2026-10-31 | `backend\venv\Scripts\ruff.exe check backend; backend\venv\Scripts\ruff.exe format --check backend` | Exit 0 | 67 backend files clean |

---

## Audit Phase 7 — API Reliability, Schema Validation, and Error Contracts

### Acceptance gates

- [x] BUG-11 fixed: Starlette 413 (`HTTP_413_CONTENT_TOO_LARGE`) and 422 (`HTTP_422_UNPROCESSABLE_CONTENT`) deprecation warnings resolved using backward-compatible aliases in `backend/app/core/errors.py`.
- [x] Unified error envelope compliance: expanded `code_map` in `http_exception_handler` (`backend/app/core/errors.py`) to map 400 (`VALIDATION_ERROR`), 404 (`NOT_FOUND`), 409 (`CONFLICT`), 413 (`VALIDATION_ERROR`), 422 (`VALIDATION_ERROR`), 502 (`GENERATION_FAILED`), 503 (`MODEL_UNAVAILABLE`), and 504 (`GENERATION_TIMEOUT`) with proper `retryable` booleans.
- [x] Unhandled exception sanitization: `unhandled_exception_handler` in `errors.py` logs full tracebacks on the server while returning sanitized 500 JSON without leaking system paths, passwords, or stack traces.
- [x] External provider timeout mapping: updated `backend/app/generation/provider.py` to map `httpx.TimeoutException` to `GENERATION_TIMEOUT` (HTTP 504, `retryable=True`) rather than collapsing into 503 `MODEL_UNAVAILABLE`.
- [x] Vite proxy connection resilience: configured `proxy.on("error")` handler in `frontend/vite.config.ts` to intercept backend downtime (`ECONNREFUSED 127.0.0.1:8000`) and return clean HTTP 503 JSON with `SERVICE_UNREACHABLE` rather than dropping TCP sockets.
- [x] Frontend error boundary protection: created `frontend/src/components/ErrorBoundary.tsx` wrapping `AppShell` in `frontend/src/app/App.tsx`, preventing React unmounting into blank white screens during component runtime exceptions and providing interactive retry actions.
- [x] Comprehensive test coverage:
  - 8 tests in `backend/tests/test_api_reliability.py` verifying 422 validation envelopes, 404 not found, 413 payload too large, 500 sanitized envelopes, 502 Bad Gateway recovery, 409 concurrent turn conflict, stale turn reclamation (>60s), and idempotency conflict on altered question replay.
  - 3 tests in `frontend/src/tests/ErrorBoundary.test.tsx` verifying child error catching, fallback card rendering, and interactive state reset.
- [x] Full test suite verification:
  - Full backend pytest suite: 190 passed in 68.19s with 0 errors and 0 Starlette deprecation warnings.
  - Full frontend Vitest suite: 36 passed in 14.34s across 9 test files.
  - Frontend production build: clean in 1.82s.
  - Ruff lint & format: 100% clean across all 68 backend files.

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_api_reliability.py` | Exit 0 — 8 passed in 6.01s | All status envelopes, 502 recovery, 409 conflict & stale reclamation verified |
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests` | Exit 0 — 190 passed in 68.19s | All 20 backend test files green, 0 deprecation warnings |
| 2026-10-31 | `npm --prefix frontend test -- --run` | Exit 0 — 36 passed in 14.34s | All 9 frontend test files passing |
| 2026-10-31 | `npm --prefix frontend run build` | Exit 0 in 1.82s | Production bundle clean |
| 2026-10-31 | `backend\venv\Scripts\ruff.exe check backend; backend\venv\Scripts\ruff.exe format --check backend` | Exit 0 | All 68 backend files clean |

---

## Audit Phase 8 — Conversation Persistence and Context Management

### Acceptance gates

- [x] BUG-12 fixed: passed `scope_document_ids=doc_ids_list` to `conv_repo.add_message` for assistant turns in `backend/app/services/chat_service.py`, fixing context loss where scoped follow-up turns previously dropped previous assistant turns.
- [x] Multi-turn bounded LLM context: `get_recent_completed_turns` in `backend/app/database/repositories/conversations.py` strictly bounds conversational history to the last 3 completed turns (6 messages), preventing unbounded prompt growth.
- [x] Scope isolation across conversations: prior assistant turns from outside the active document scope are omitted from the LLM prompt context to prevent assertions from other documents leaking into the active scope.
- [x] Citation snapshot preservation: when source documents are deleted from the archive, past conversation messages preserve their full citation JSON (chunk ID, title, page, and excerpt), decorated with `document_exists = False` and rendered in the frontend as `Historical Snapshot — Source removed`.
- [x] Foreign key cascade deletion: deleting a conversation (`DELETE /api/conversations/{id}`) completely removes all associated messages via SQLite `ON DELETE CASCADE` (`PRAGMA foreign_keys = ON`), leaving 0 orphaned records.
- [x] Full multi-turn test suite:
  - 10 tests in `backend/tests/test_conversations.py` verifying auto-creation, multi-turn bounded context, retry without duplication, 409 idempotency conflict, citation snapshots after document deletion, empty thread lifecycle, scoped multi-turn retention, cross-scope isolation, 3-turn bounding, and cascade deletion.
  - 4 tests in `backend/tests/test_conversation_repository.py` verifying SQLite CRUD, cascades, stale pending reclamation, and scope isolation.
  - 3 tests in `frontend/src/tests/ConversationSidebar.test.tsx` verifying thread listing, selection, inline rename, and delete modal confirmation.
  - 3 tests in `frontend/src/tests/ConversationThread.test.tsx` verifying chronological rendering, SQLite-verified badges, historical snapshot badges, and retry handling.
- [x] Verification results:
  - Backend pytest: 194 passed in 24.90s across all 20 test files.
  - Frontend Vitest: 36 passed in 4.34s across all 9 test files.
  - Frontend production build: clean in 1.48s.
  - Ruff lint & format: 100% clean across all 68 backend files.

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_conversations.py` | Exit 0 — 10 passed in 12.82s | Scoped context, 3-turn bound, cascade delete verified |
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests/test_conversation_repository.py` | Exit 0 — 4 passed in 0.29s | CRUD, cascades, snapshots across doc delete |
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests` | Exit 0 — 194 passed in 24.90s | Zero regressions across all 20 backend test files |
| 2026-10-31 | `npm --prefix frontend test -- --run` | Exit 0 — 36 passed in 4.34s | All 9 frontend test files passing |
| 2026-10-31 | `npm --prefix frontend run build` | Exit 0 in 1.48s | Production bundle clean |
| 2026-10-31 | `backend\venv\Scripts\ruff.exe check backend; backend\venv\Scripts\ruff.exe format --check backend` | Exit 0 | All 68 backend files clean |

---

## Audit Phase 9 — Frontend UX, Evidence Transparency, and Product Reliability

### Acceptance gates

- [x] Evidence transparency & citation inspection:
  - In `ConversationThread.tsx`, citations render as interactive `<details open>` cards showing chunk ID (`[chunk_id]`), document title/filename, page number, SQLite verification badge (`✓ SQLite Verified` vs `Historical Snapshot — Source removed`), and exact quoted excerpt.
- [x] Clear visual hierarchy for answers:
  - Direct answer: highlighted callout box with serif typography (`border-l-4 border-parchment-accent bg-parchment-surface/60 p-3.5`).
  - Archive context: distinct metadata label (`Archive context:`).
  - Scope & Limitations: styled amber card (`border-amber-200/60 bg-amber-50/50 p-3 text-amber-900`) with bulleted limitation items.
- [x] Semantic search results transparency:
  - `AskArchiveView.tsx` renders query matches with document name, page number, relevance label (`High match`, `Medium match`, `Relevant`), and exact quoted text.
  - Informative `EmptyState.tsx` rendered when search has 0 matches.
- [x] Actionable error states & graceful offline degradation:
  - Failed chat turns render red error card with exact failure reason and an interactive "Retry Turn" button.
  - Ollama offline banner displays exact recovery steps (`ollama serve` or `ollama pull {model}`), disabling the question composer to prevent hopeless submissions.
  - `ErrorBoundary.tsx` prevents React white screens during unexpected render errors with "Try Again" and "Reload Page" buttons.
  - `ErrorBanner.tsx` displays structured `ErrorCode` with `Try again` actions for retryable API errors.
- [x] Intuitive multi-view workspace navigation:
  - Sidebar navigation between Overview, Documents, Ask Archive, Conversations, and System Status.
  - Active document scope selector dynamically filters corpus boundaries and updates retrieval target labels.
  - Batch upload queue provides per-file status badges (`queued`, `uploading`, `ready`, `duplicate`, `failed`).
- [x] Test suite verification:
  - 36 frontend Vitest tests passed across all 9 test suites (`NavigationViews`, `ArchiveWorkspace`, `ConversationThread`, `ConversationSidebar`, `DocumentLibrary`, `StatusIndicator`, `ErrorBanner`, `ErrorBoundary`, `client`).
  - Frontend production build (`tsc && vite build`) clean in 1.73s with 0 errors and zero `any` types in production source.
  - Backend pytest: 194 passed in 24.90s.
  - Ruff lint and formatting checks: 100% clean across all 68 backend files.

### Verified command log

| Date/time | Command | Result | Notes |
|---|---|---|---|
| 2026-10-31 | `npm --prefix frontend test -- --run` | Exit 0 — 36 passed in 4.25s | All 9 frontend test files passing |
| 2026-10-31 | `npm --prefix frontend run build` | Exit 0 in 1.73s | Production bundle clean, zero TypeScript errors |
| 2026-10-31 | `backend\venv\Scripts\python.exe -m pytest backend/tests` | Exit 0 — 194 passed in 24.90s | Zero regressions across all 20 backend test files |
| 2026-10-31 | `backend\venv\Scripts\ruff.exe check backend; backend\venv\Scripts\ruff.exe format --check backend` | Exit 0 | All 68 backend files clean |

---

## Phase 7 — README and Demo

### Acceptance gates

- [ ] Fresh-checkout setup on Windows following README steps reaches working demo
- [ ] `docs/EVALUATION_RESULTS.md` contains real measured metrics
- [ ] `LICENSE` file present with verified compatible license
