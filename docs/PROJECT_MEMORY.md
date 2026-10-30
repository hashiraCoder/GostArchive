# GhostArchive — Project Memory

> Durable implementation facts. Updated only after a phase is verified (real commands run, real output confirmed). Do not store planned state as done. Do not duplicate specs. Separate planned / implemented / tested states clearly.

## Repository identity

- **Project name:** GhostArchive
- **Repository path:** `d:\main_projects\GostArchive`
- **Primary branch:** `main`
- **Language/runtime:** Python 3.11+, TypeScript (Node 18/20 LTS)
- **Stack settled:** FastAPI + SQLite (with FTS5) + ChromaDB (cosine space) + SentenceTransformers + Ollama + React/Vite/Tailwind

## Verified implementation state

### Phase 0 — Repository Foundations
- **Status:** ✅ Complete — commit `5749358`
- **Completed items (verified):**
  - All `ai_md/` spec documents exist and are the canonical spec source
  - `.gitignore` created — covers Python, data dir, SQLite, Chroma, model files, node_modules, .env; verified with `git check-ignore`
  - `.gitattributes` created — normalizes line endings to LF
  - `.env.example` created — all configurable env vars with safe defaults, documented
  - `README.md` created — honest status (nothing implemented yet), prerequisites, privacy notes, license caveats
  - `AGENTS.md` created at repo root (mirrors `ai_md/AGENTS.md` for tooling)
  - `docs/PROJECT_MEMORY.md` — this file
  - `docs/PHASE_CHECKLIST.md` — acceptance gate ledger
  - `docs/DECISIONS.md` — architecture decisions log (D-01 through D-08)
  - `data/sample_archive/` — 8 synthetic fictional documents (all evaluation categories)
  - `data/evaluation/questions.json` — 20 labeled evaluation questions (all 7 categories)
  - **Commit:** `5749358` on branch `main`, 35 files, 2363 insertions

### Phase 1 — Frontend/backend skeleton and health check
- **Status:** ✅ Complete — verified 2026-10-29
- **Completed items (verified):**
  - FastAPI application with loopback-only CORS and `/api/health`
  - `/api/ready` reports SQLite, Chroma storage, embedding package, and Ollama/model status independently
  - React/Vite shell with polling status indicator and loading/error states
  - StatusIndicator coverage for ready, degraded, and unavailable dependency states
  - Backend health tests: 9 passed
  - Frontend tests: 11 passed
  - Frontend TypeScript check and production build passed
  - Ruff lint and formatting checks passed
- **Important limitation:** The current environment reports embedding and Ollama dependencies as degraded until their runtime packages/model are installed.

### Phase 2 — Document ingestion and SQLite persistence
- **Status:** ✅ Complete — verified 2026-10-29
- **Completed items (verified):**
  - SQLite schema for documents and chunks with foreign keys and indexes
  - UTF-8 `.txt` and `.md` validation with configurable byte/text limits
  - Server-generated UUID storage names; uploaded filenames remain display metadata
  - Newline/control-character normalization and deterministic bounded chunking with offsets
  - SHA-256 duplicate detection returning the existing document with `duplicate: true`
  - Document upload, list, detail, and delete endpoints
  - Recoverable delete lifecycle using `deleting` state before source-file cleanup
  - Backend tests: 15 passed; frontend tests: 11 passed
- **Scope boundary:** Embeddings and Chroma vector persistence are intentionally deferred to Phase 3.

### Phase 3 — Embeddings, Chroma persistence, and semantic search
- **Status:** ✅ Complete — verified 2026-10-29
- **Completed items (verified):**
  - Local Sentence Transformers provider with lazy model loading
  - Persistent Chroma adapter storing SQLite chunk IDs and minimal metadata
  - Bounded semantic search endpoint with optional document filtering
  - SQLite-authoritative result resolution and orphan-vector dropping
  - SQLite-to-Chroma rebuild helper
  - Real paraphrase retrieval and persistence test passed
  - Backend tests: 22 passed; frontend tests: 11 passed
  - Installed retrieval dependencies: `sentence-transformers==6.2.0`, `chromadb==1.5.9`
- **Scope boundary:** Grounded Ollama generation and citation validation remain Phase 4.

### Phase 4 — Grounded Q&A with Ollama and citation validation
- **Status:** ✅ Complete — verified 2026-10-29
- **Completed items (verified):**
  - Local Ollama `/api/chat` client with timeout and explicit unavailable/generation errors
  - Prompt framing that treats document text as untrusted quoted evidence
  - JSON output validation with citation IDs restricted to retrieved chunks
  - SQLite-authoritative citation metadata returned by `POST /api/chat`
  - Explicit insufficient-evidence behavior for empty retrieval and model abstention
  - Mocked Ollama tests for answerable, unanswerable, unavailable, malformed, hallucinated-citation, and injection cases
  - Backend tests: 28 passed; Ruff lint and formatting checks passed
- **Scope boundary:** React evidence presentation and complete UI state handling remain Phase 5.

### Phase 5 — Evidence UI and product polish
- **Status:** ✅ Implemented; manual runtime flow pending
- **Completed items (verified):**
  - React document library with upload, empty, loading, error, and confirmed deletion states
  - Semantic search UI with loading, empty-result, and error states
  - Grounded question UI with model-offline error handling, insufficient-evidence messaging, and trusted citation expansion
  - Centralized typed API clients for documents, search, and chat
  - Frontend tests: 13 passed; TypeScript/Vite production build passed
  - Backend regression tests: 28 passed
- **Pending verification:** Manual import → search → ask → citation → delete → restart flow requires local embedding and Ollama services.

### Phase 6 — Tests and deterministic evaluation
- **Status:** ✅ Complete — verified 2026-10-29
- **Completed items (verified):**
  - Deterministic evaluation runner at `backend/app/evaluation/runner.py`
  - Portable 20-question synthetic evaluation dataset with all 8 observed categories
  - Dataset integrity checks for IDs, categories, source files, and expected answer phrases
  - Real evaluation output: 20 questions, 9 corpus documents, 100% source coverage, 100% phrase coverage, 0.9333 lexical source hit@5
  - Backend tests: 30 passed; frontend tests: 13 passed
  - Ruff lint and formatting checks passed
- **Scope boundary:** Metrics are an offline lexical/source-coverage baseline, not an Ollama answer-quality benchmark.

### RAG Remediation — Retrieval & Answer Quality Overhaul
- **Status:** ✅ Complete — verified 2026-10-30
- **Completed items (verified):**
  - Chroma collection metadata configured with explicit `"hnsw:space": "cosine"` metric
  - SQLite FTS5 full-text search table (`document_chunks_fts`) added and maintained across document ingestion, rebuild, and deletion
  - Hybrid retrieval combining Chroma cosine similarity and SQLite FTS5 BM25 with Reciprocal Rank Fusion (RRF)
  - Calibrated minimum relevance threshold (`0.30` cosine similarity) separating true relevant hits from out-of-domain noise
  - Negative percentages (`-80% match`) eliminated; replaced with descriptive relevance labels ("High match", "Medium match", "Relevant") and bounded scores
  - Clear empty-state messaging for irrelevant queries in both Search and Ask
  - Sentence-boundary-aware chunking preserving paragraphs and complete sentences
  - Redesigned system prompt adhering to 10 strict grounding principles for local small models (`gemma3:1b`)
  - Structured output schema (`direct_answer`, `archive_context`, `limitations`, `citations`, `insufficient_evidence`) with trusted SQLite citation validation
  - Dedicated archive & document summary capability (`POST /api/summarize`) distinct from Search and Ask
  - Backend test suite: 37 passed in 13.73s
  - Frontend vitest suite: 13 passed, production build passed
  - Ruff lint and formatting checks: 100% passed

### Phase P0 — Core Integrity Remediation (Deletion Idempotency & Summary Scope)
- **Status:** ✅ Complete — verified 2026-10-30
- **Completed items (verified):**
  - Idempotent delete implementation: `DELETE /api/documents/{id}` safely returns 204 No Content on existing, already deleted, or missing IDs without throwing 404 errors.
  - Safe multi-store resource cleanup: `remove_document()` in `backend/app/services/document_service.py` ensures storage file unlinking, Chroma vector deletion, FTS5 cleanup, and SQLite row removal.
  - Frontend optimistic row-locking & error banner suppression: `ArchiveWorkspace.tsx` and `DocumentLibrary.tsx` disable delete buttons during in-flight operations and gracefully sync local state if the server reports a document already deleted.
  - Multi-document archive summary scope fix: `summarize_archive()` in `backend/app/services/summary_service.py` fairly iterates across all ready documents with balanced per-document chunk budgeting rather than breaking prematurely.
  - Accurate summary scope reporting: Scope string explicitly reports inspected ready documents out of total ready documents (`"covering X of Y ready documents"`), and any unready or failed documents are reported in `limitations`.
  - Backend tests: `test_summary.py` (4 passed), `test_documents.py -k test_list_and_delete_document` (passed).
  - Frontend tests: 14 passed (including 204 No Content client test); Vite production build: 0 errors.
  - Browser DevTools verification: 204 No Content empty-body parsing fixed in `client.ts`; document deleted and removed from UI immediately without false "try again" banner.
  - Storage integrity verified: 0 documents, 0 chunks, 0 FTS rows, 0 Chroma vectors, 0 stored files.

### Phase P1 — Intelligence & Intent Routing (Issue D & Issue E Remediation)
- **Status:** ✅ Complete — verified 2026-10-30
- **Completed items (verified):**
  - Query intent classification: `classify_query_intent` in `backend/app/services/intent_service.py` classifies user queries into `GREETING`, `ARCHIVE_SUMMARY`, `ARCHIVE_QUESTION`, and `OFF_TOPIC`.
  - Conversational routing: User pleasantries (e.g., "hello", "who are you") receive immediate helpful guidance without running vector similarity search or reporting "insufficient evidence".
  - Automatic summary routing: Broad archive questions ("what this archive says", "summarize my notes") are routed directly into the archive summarizer rather than pulling arbitrary top-k technical chunks.
  - Off-topic protection: Out-of-domain prompts (e.g. code generation, jokes) receive clear, polite refusal explaining GhostArchive's memory retrieval boundary.
  - Deep operational health diagnostics: `backend/app/api/routes/health.py` enhanced to verify SQLite schema tables, Chroma collection querying, and SentenceTransformers local weight caching status (`ready` vs `degraded`).
  - Test suites: 18 intent unit tests passed, 17 chat/health tests passed, 13 frontend vitest tests passed, Vite build passed with 0 errors.
  - Ruff lint & format: 100% clean across 51 backend files.

### Phase P2 — UX & Evidence Transparency (Badges, Citations, Structured Answers)
- **Status:** ✅ Complete — verified 2026-10-30
- **Completed items (verified):**
  - Document status styling: visual badges reflecting exact status (`ready`, `processing`, `deleting`, `error`) with import dates.
  - Search relevance badges: color-coded match indicators (`High match`, `Medium match`, `Relevant`) with char spans.
  - Grounded answer presentation: Direct Answer callout boxes, archive context, explicit scope & limitations, and expandable citation cards with SQLite-verified chunk IDs.
  - Test suites: 13/13 frontend vitest tests passed, Vite production build clean, 39 backend tests passed.

### Phase P3 — Extensible Model Architecture (Optional Provider Protocol)
- **Status:** ✅ Complete — verified 2026-10-30
- **Completed items (verified):**
  - Abstract `LLMProvider` protocol in `backend/app/generation/provider.py`.
  - `OllamaClient` adapts to `LLMProvider` with dynamic `model_name`.
  - `ExternalLLMProvider` enables optional cloud API keys (Gemini / OpenAI-compatible) with clear error envelopes.
  - Safe local defaults: `get_llm_provider` defaults strictly to local Ollama (100% offline). If external is specified without key, it safely falls back to Ollama with a warning.
  - `chat_service.py` and `summary_service.py` accept and use `LLMProvider`.
  - Settings and `.env.example` updated with privacy notice.
  - 44 backend unit tests pass in 8.22s, 13 frontend tests pass, 53 files clean lint and format.

### Phase 7–10
- **Status:** Not started

## Key configuration defaults (from .env.example)

| Setting | Default | Note |
|---|---|---|
| `GHOSTARCHIVE_HOST` | `127.0.0.1` | Loopback only — never 0.0.0.0 |
| `GHOSTARCHIVE_PORT` | `8000` | |
| `GHOSTARCHIVE_DATA_DIR` | `backend/data` | Runtime only; gitignored |
| `UPLOAD_MAX_BYTES` | `5242880` (5 MiB) | Configurable |
| `EXTRACTED_TEXT_MAX_CHARS` | `500000` | |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Loopback only |
| `OLLAMA_MODEL` | `gemma3:1b` | Gemma Terms of Use apply |
| `OLLAMA_TIMEOUT_SECONDS` | `60` | |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Apache-2.0; downloads on first use |
| `RETRIEVAL_TOP_K` | `5` | Clamped 1–8 |
| `RETRIEVAL_TOP_K_MAX` | `8` | Hard cap |
| `RETRIEVAL_MIN_SIMILARITY` | `0.30` | Calibrated threshold; rejects noise |
| `RETRIEVAL_LEXICAL_BOOST` | `true` | SQLite FTS5 BM25 + RRF |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Vite dev server only |
| `LOG_LEVEL` | `INFO` | Never log document content |

## Architectural decisions summary

See `docs/DECISIONS.md` for full rationale.

| ID | Decision |
|---|---|
| D-01 | Python 3.11+ (3.12 if all deps support it) |
| D-02 | SQLite is authoritative for all metadata; Chroma is rebuildable index only |
| D-03 | API bound to `127.0.0.1`; CORS allows loopback Vite origin only |
| D-04 | No cross-store transactions; use explicit compensation and `deleting` state |
| D-05 | Sample archive uses synthetic fictional content only |
| D-06 | `top_k` default 5, hard cap 8; similarity threshold calibrated to 0.30 |

## Open decisions (user input needed)

| # | Question | Default assumed | Notes |
|---|---|---|---|
| D-07 | Project license | TBD | Must be compatible with all deps |
| D-08 | Node.js version | 20 LTS | Used for frontend |

## Known issues

None recorded yet.

## Verified command log

| Date | Command | Result | Notes |
|---|---|---|---|
| 2026-10-29 | Initial repo inspection | Fresh repo, only `ai_md/` present | No commits yet |
| 2026-10-29 | `git check-ignore` on 7 patterns | All 6 sensitive patterns correctly blocked; sample archive not blocked | `.gitignore` verified |
| 2026-10-29 12:22 | `git commit 5749358` | 35 files, 2363 insertions, exit 0 | Phase 0 complete |
| 2026-10-29 19:05 | Backend pytest, frontend Vitest/build, and local smoke checks | Passed | Phase 1 behavior verified |
| 2026-10-29 19:08 | Ruff format and format check | Passed | Backend source and tests formatted cleanly |
| 2026-10-29 21:34 | Phase 2 backend/frontend validation | Passed | 15 backend tests, 11 frontend tests, frontend build, Ruff checks |
| 2026-10-29 22:13 | Phase 3 backend validation | Passed | 22 backend tests |
| 2026-10-29 22:15 | Phase 3 frontend validation | Passed | 11 frontend tests and production build |
| 2026-10-29 | Phase 4 backend validation | Passed | 28 tests |
| 2026-10-29 | Phase 5 frontend validation | Passed | 13 frontend tests, production build |
| 2026-10-29 | Phase 6 validation | Passed | 30 backend tests, 13 frontend tests |
| 2026-10-30 | Calibration & RAG remediation | Passed | Measured cosine similarity baseline on sample archive |
| 2026-10-30 | `backend\venv\Scripts\python.exe -m pytest backend\tests --tb=short` | Exit 0 — 37 passed in 13.73s | All 37 backend tests passed |
| 2026-10-30 | `npm --prefix frontend test` | Exit 0 — 13 passed in 2.51s | All 13 frontend tests passed |
| 2026-10-30 | `npm --prefix frontend run build` | Exit 0 | TypeScript check and Vite production build passed |
| 2026-10-30 | `backend\venv\Scripts\ruff.exe check backend\app backend\tests` | Exit 0 — All checks passed | Clean lint |
| 2026-10-30 | `backend\venv\Scripts\ruff.exe format --check backend\app backend\tests` | Exit 0 | Clean format |
