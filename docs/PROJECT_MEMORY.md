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

### Controlled Implementation — Steps 1–4 (Scope, Multi-file, Document Management, Error States)
- **Status:** ✅ Complete — verified 2026-10-30
- **Completed items (verified):**
  - Archive Scope Selection:
    - Scope selector dropdown supporting `Entire Archive` and individual documents.
    - Active scope badge with clear reset controls.
    - Scope switching invalidates and resets stale search and chat results.
    - `document_ids` passed cleanly through `searchDocuments()` and `askQuestion()`.
    - Retrieval scope isolation verified by test: queries restricted to Document B never return passages from Document A.
  - Multi-File Upload & Batch Queue:
    - Drag-and-drop zone and multi-file selection support.
    - Controlled sequential processing queue uploading one file at a time without loading entire batch into memory.
    - Per-file progress tracking (`queued`, `uploading`, `ready`, `duplicate`, `failed`).
    - Duplicate detection preserves existing entries with `duplicate: true`.
    - Partial failures handled gracefully with individual retry actions and completed imports preserved.
  - Document Management:
    - Server-side and client-side filtering by filename query, status (`ready`, `processing`, `error`), and file type (`txt`, `md`).
    - Pagination controls with 10 documents per page.
    - Individual selection checkboxes and master select-all on page.
    - Bulk deletion modal confirmation and execution with per-document result reporting (`POST /api/documents/bulk-delete`).
    - Selection and page bounds remain consistent post-deletion.
  - Error and Empty States:
    - Dedicated Ollama offline alert banner in Ask section with disabled question submission when Ollama is unavailable.
    - Active indexing status notice explaining partial results while documents are processing.
    - Enhanced search empty state using `EmptyState.tsx` with query refinement guidance.
    - Documents remain in `processing` until vector storage completes, never prematurely labeled `ready`.
  - Test suites:
    - 81 backend pytest tests passed in 25.84s.
    - 18 frontend Vitest tests passed in 2.69s.
    - Vite production build cleanly succeeds in 2.37s.
    - Ruff check & format clean across all 54 backend files.

### Model Readiness & Health Decoupling
- **Status:** Complete (2026-10-30)
- **Problem Resolved:** Addressed contradiction where `GET http://127.0.0.1:11434/api/tags` returned 200 and document batch upload succeeded (12/12 `ready`), but `POST /api/chat` failed with `MODEL_UNAVAILABLE (Retryable): The local Ollama service is unavailable`.
- **Key Changes:**
  - Separated health checks into 5 distinct sub-systems: `ollama_service` (HTTP reachability), `model_available` (model tag presence), `model_inference` (generation probe, lightweight by default or bounded 5s via `?check_inference=true`), `embedding_service` (local embeddings), and `document_storage` (SQLite + Chroma).
  - Fine-grained exception & error mapping in `OllamaClient`:
    - `httpx.ConnectError` -> `MODEL_UNAVAILABLE` (503, `retryable=True`)
    - HTTP 404 / missing model -> `MODEL_NOT_FOUND` (503, `retryable=False`, actionable `ollama pull {model}`)
    - `httpx.TimeoutException` -> `GENERATION_TIMEOUT` (504, `retryable=True`)
    - HTTP 500 / OOM / crash -> `GENERATION_FAILED` (502, `retryable=False`)
  - Updated frontend `StatusIndicator` and `ArchiveWorkspace` to distinguish daemon offline (`ollama serve`) from model missing (`ollama pull {model}`) and decoupled document library readiness from LLM inference availability.
  - Added comprehensive regression test suite `backend/tests/test_model_readiness.py` covering all 9 failure and isolation scenarios.
- **Verification:**
  - 9/9 regression tests in `test_model_readiness.py` passed in 21.70s.
  - 90/90 backend pytest tests passed in 26.72s.
  - 18/18 frontend Vitest tests passed in 3.00s.
  - Frontend production build (`tsc && vite build`) passed in 2.29s.
  - Ruff lint & format checks clean across all 55 files.

### Phase P0 — Conversation Persistence (Multi-Turn Discussions, Idempotency, Snapshots)
- **Status:** Complete (2026-10-31)
- **Completed items (verified):**
  - Extended SQLite relational schema with foreign key enforcement (`PRAGMA foreign_keys = ON;`):
    - `conversations` (id, title, timestamps).
    - `messages` (id, conversation_id with ON DELETE CASCADE, client_turn_id, role, content, status, direct_answer, archive_context, limitations, insufficient_evidence, citations, retrieval_count, model, error_message, scope_document_ids, timestamps).
    - Indices on updated_at, conversation_id, and (conversation_id, client_turn_id) for performance and idempotency.
  - Multi-Turn Bounded LLM Context & Evidence Separation:
    - Passes bounded history (last 3 completed turns) to `gemma3:1b` for reference and pronoun resolution without treating past assistant answers as ground truth evidence.
    - Excludes active turn question from history to prevent duplication in prompt framing.
  - Scope Isolation:
    - Persists document scope on every user turn.
    - Automatically filters out assistant turns from incompatible or broader document scopes when a query is narrowed to specific documents.
  - Idempotency & Concurrency:
    - Prevents duplicate inference on matching `client_turn_id` within conversation.
    - Replaying a completed turn idempotently returns the saved response.
    - Reusing an idempotency key with a different question rejects with HTTP 409 Conflict.
    - Concurrent turns in the same conversation locked via pending checks (HTTP 409).
    - Stale pending turns (>60s) from crashes automatically recovered and marked failed.
  - Explicit Message State Transitions & Retry:
    - User message: `completed`.
    - Assistant message: `pending` -> `completed` or `pending` -> `failed`.
    - Retrying a failed turn updates existing assistant message (`failed` -> `pending` -> `completed`) without duplicating user messages.
  - Self-Contained Citation Snapshots:
    - Citations preserved in full JSON snapshot.
    - Thread loader verifies document existence: removed documents flagged as `Historical Snapshot — Source removed` (`document_exists: false`).
  - Full Dedicated UI:
    - `ConversationSidebar`: search conversations, + New Conversation, inline rename, delete confirmation modal.
    - `ConversationThread`: chronological cards, pending pulsing indicator, failed turn alert with "Retry Turn" button, expandable citations with verification badges.
  - Test suites:
    - 100 backend pytest tests passed in 66.40s.
    - 24 frontend Vitest tests passed in 5.76s.
    - Frontend build: clean in 2.03s.
    - Ruff lint and formatting checks: 100% clean across all 61 files.

### Audit Phase 5 — Grounded Generation & Evidence Adherence
- **Status:** Complete (2026-10-31)
- **Completed items (verified):**
  - Repaired small model self-contradiction (BUG-05): implemented `_is_contradictory_limitation` in `backend/app/generation/output_validation.py` to suppress false negative limitation claims when the target entity/topic is accurately answered in `answer` and supported in evidence.
  - Implemented schema normalization for 1B parameter models: gracefully handles omitted or string-typed `insufficient_evidence` and `cited_chunk_ids` keys, eliminating HTTP 502 schema crashes.
  - Multi-tier citation resolution: resolves exact chunk IDs, document UUID prefix matches, and content fallback lexical matching against retrieved passages, ensuring real database chunk citations are linked while ungrounded hallucinations (0 overlap) strictly abstain.
  - Grounding prompt principles: enhanced `SYSTEM_PROMPT` in `backend/app/generation/prompts.py` with Grounding Principles 7, 8, and 9 (consistency rule, code syntax evidence rule, and exact chunk ID copying instructions).
  - Test suites:
    - `backend/tests/test_grounded_generation.py`: 7/7 tests passed in 0.03s.
    - Live Gemma 3 1B benchmark verified on 7 test questions: 0 crashes, 0 hallucinated citations, accurate answers and clean abstentions.
    - Full backend pytest suite: 171 passed in 23.75s across all 17 test suites.
    - Full frontend Vitest suite: 33 passed in 5.09s across all 8 test suites.
    - Frontend production build: clean in 1.46s.
    - Ruff lint and format: 100% clean across 65 backend files.

### Audit Phase 6 — Mathematical and Code Reasoning
- **Status:** Complete (2026-10-31)
- **Completed items (verified):**
  - Fixed small LLM arithmetic and code reasoning hallucinations (BUG-10) by implementing deterministic extraction and computation in `backend/app/generation/math_reasoning.py`:
    - `extract_signal_parameters`: parses variables (`fm = 5 Hz`, `fs = 20 Hz`) and colon vectors (`t = 0:0.001:1`, `ts = 0:Ts:1`, `n = 0:1/fs:1`), computing Nyquist rate (10 Hz), sampling interval ($T_s = 0.05\text{ s}$), original samples (1001 points), and sampled points (21 points).
    - `analyze_math_question`: evaluates questions for specific calculations (Nyquist rate, sampling interval, sample counts, sufficiency check, colon vector syntax, and frequency checks like 8 Hz aliasing).
    - `analyze_code_identifiers`: detects MATLAB commands (`clc`, `clear`, `close all`, `interp1`, `stem`) present in evidence passages and provides verified semantic explanations grounded in the script.
  - Injected verified derived calculations into prompt directives in `backend/app/generation/prompts.py`.
  - Added deterministic math and code validation in `validate_model_output` (`output_validation.py`), correcting arithmetic hallucinations and attaching derived citations with `evidence_type = "derived"`.
  - Test suites:
    - `backend/tests/test_math_reasoning.py`: 11/11 tests passed in 0.06s.
    - All 7 benchmark mathematical and code calculations verified on live Gemma 3 1B with 100% numerical accuracy.
    - Full backend pytest suite: 182 passed in 29.53s across all 18 test suites.
    - Full frontend Vitest suite: 33 passed in 5.86s across all 8 test suites.
    - Frontend production build: clean in 4.14s.
    - Ruff lint and format: 100% clean across 67 backend files.

### Audit Phase 7 — API Reliability, Schema Validation & Error Contracts
- **Status:** Complete (2026-10-31)
- **Completed items (verified):**
  - Repaired Starlette 413 and 422 deprecation warnings (BUG-11): defined `HTTP_413_CONTENT_TOO_LARGE` and `HTTP_422_UNPROCESSABLE_CONTENT` in `backend/app/core/errors.py`.
  - Unified Error Envelope across all HTTP statuses: expanded `code_map` in `http_exception_handler` to properly map 400 (`VALIDATION_ERROR`), 404 (`NOT_FOUND`), 409 (`CONFLICT`), 413 (`VALIDATION_ERROR`), 422 (`VALIDATION_ERROR`), 502 (`GENERATION_FAILED`), 503 (`MODEL_UNAVAILABLE`), and 504 (`GENERATION_TIMEOUT`) with accurate `retryable` properties.
  - Sanitized internal error logging: `unhandled_exception_handler` logs internal tracebacks without exposing server paths, passwords, or stack traces to API clients.
  - External provider timeout mapping: updated `backend/app/generation/provider.py` to map `httpx.TimeoutException` to `GENERATION_TIMEOUT` (HTTP 504, `retryable=True`).
  - Vite proxy connection resilience: configured `proxy.on("error")` handler in `frontend/vite.config.ts` to convert `ECONNREFUSED 127.0.0.1:8000` into structured HTTP 503 JSON (`SERVICE_UNREACHABLE`).
  - Frontend error boundary protection: implemented `frontend/src/components/ErrorBoundary.tsx` wrapping the application in `App.tsx` with error alert card and interactive retry buttons, preventing white-screen crashes.
  - Test suites:
    - `backend/tests/test_api_reliability.py`: 8/8 passed in 6.01s (422 validation, 404 not found, 413 payload too large, 500 sanitized envelope, 502 Bad Gateway recovery, 409 concurrent turn conflict, stale turn reclamation >60s, idempotency conflict).
    - `frontend/src/tests/ErrorBoundary.test.tsx`: 3/3 passed in 1.05s.
    - Full backend pytest suite: 190 passed in 68.19s across all 20 backend test suites with 0 deprecation warnings.
    - Full frontend Vitest suite: 36 passed in 14.34s across all 9 frontend test suites.
    - Frontend production build: clean in 1.82s.
    - Ruff lint and format: 100% clean across all 68 backend files.

### Audit Phase 8 — Conversation Persistence & Context Management
- **Status:** Complete (2026-10-31)
- **Completed items (verified):**
  - Repaired scoped follow-up context loss (BUG-12): passed `scope_document_ids=doc_ids_list` to `conv_repo.add_message` for assistant turns in `backend/app/services/chat_service.py`, ensuring previous assistant responses in the same document scope are retained for reference and pronoun resolution.
  - Multi-turn bounded LLM context: `get_recent_completed_turns` strictly caps history to the last 3 completed turns (6 messages), preventing unbounded prompt token expansion.
  - Document scope isolation across turns: queries narrowed to specific documents omit out-of-scope assistant assertions from prompt context, preventing cross-document hallucination.
  - Snapshot integrity across document deletions: citations stored in full JSON snapshots remain viewable even if source documents are deleted from SQLite, decorated with `document_exists = False` and rendered in the UI as `Historical Snapshot — Source removed`.
  - Cascading deletion: `DELETE /api/conversations/{id}` completely removes all associated messages via SQLite foreign key cascading without orphaned rows.
  - Test suites:
    - `backend/tests/test_conversations.py`: 10/10 passed in 12.82s.
    - `backend/tests/test_conversation_repository.py`: 4/4 passed in 0.29s.
    - `frontend/src/tests/ConversationSidebar.test.tsx`: 3/3 passed in 0.42s.
    - `frontend/src/tests/ConversationThread.test.tsx`: 3/3 passed in 0.41s.
    - Full backend pytest suite: 194 passed in 24.90s across all 20 test files.
    - Full frontend Vitest suite: 36 passed in 4.34s across all 9 test files.
    - Frontend production build: clean in 1.48s.
    - Ruff lint and format: 100% clean across all 68 backend files.

### Audit Phase 9 — Frontend UX, Evidence Transparency & Product Reliability
- **Status:** Complete (2026-10-31)
- **Completed items (verified):**
  - Interactive citation accordions: `ConversationThread.tsx` renders citations as `<details open>` cards containing chunk IDs (`[chunk_id]`), document title/filename, page number, SQLite verification status (`✓ SQLite Verified` vs `Historical Snapshot — Source removed`), and exact quoted excerpts.
  - Visual hierarchy: distinct presentation for direct answers (accent-bordered callout), archive context, and scope & limitations (amber callout with bulleted items).
  - Search transparency: `AskArchiveView.tsx` displays relevance score badges (`High match`, `Medium match`, `Relevant`) alongside chunk text and metadata.
  - Actionable error and offline states: failed turns render retry buttons, Ollama offline states provide actionable instructions and disable composers safely, and `ErrorBoundary.tsx` guards the component tree against uncaught render exceptions.
  - View navigation: intuitive navigation across Overview, Documents, Ask Archive, Conversations, and System Status with live metrics, active scope switching, and batch upload queue progress.
  - Test suites:
    - 36 frontend Vitest tests passed across all 9 test suites.
    - Frontend production build (`tsc && vite build`) clean in 1.73s.
    - Full backend pytest suite: 194 passed in 24.90s.
    - Ruff lint and formatting checks: 100% clean across all 68 backend files.

### Phase 10
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
| 2026-10-30 | Remediation regression suite (`backend/tests/test_remediation_regression.py`) | Exit 0 — 10 passed in 0.31s | Temporal, FTS stemming, noise rejection, multipart, evidence isolation verified |
| 2026-10-30 | Full backend suite (`pytest backend/tests`) | Exit 0 — 78 passed in 25.33s | All 78 tests passed, 0 failures |
| 2026-10-30 | Frontend test suite (`npm --prefix frontend test`) | Exit 0 — 14 passed in 3.68s | Client 204 handler and all UI tests passing |
| 2026-10-30 | Frontend build (`npm --prefix frontend run build`) | Exit 0 in 1.95s | TypeScript + Vite production bundle clean |
| 2026-10-30 | Ruff lint & format (`ruff check backend`, `ruff format --check backend`) | Exit 0 | 54 backend files clean |
| 2026-10-30 | Steps 1–4 Backend pytest (`pytest backend/tests`) | Exit 0 — 81 passed in 25.84s | Zero regressions; scope isolation, filters, bulk delete verified |
| 2026-10-30 | Steps 1–4 Frontend Vitest (`npm --prefix frontend test`) | Exit 0 — 18 passed in 2.69s | Scope switching, filters, bulk delete modal, Ollama offline verified |
| 2026-10-30 | Steps 1–4 Frontend build (`npm --prefix frontend run build`) | Exit 0 in 2.37s | Production bundle clean |
| 2026-10-31 | Conversation Persistence Repository (`pytest backend/tests/test_conversation_repository.py`) | Exit 0 — 4 passed in 0.28s | SQLite CRUD, cascades, snapshots across doc delete, recovery |
| 2026-10-31 | Conversation Persistence Suite (`pytest backend/tests/test_conversations.py`) | Exit 0 — 6 passed in 15.60s | Multi-turn bounded LLM context, idempotency 409, retry, auto-create |
| 2026-10-31 | Full Backend Pytest Suite (`pytest backend/tests`) | Exit 0 — 100 passed in 66.40s | Zero regressions across all 100 tests |
| 2026-10-31 | Full Frontend Vitest Suite (`npm --prefix frontend test -- --run`) | Exit 0 — 24 passed in 5.76s | Sidebar, Thread, Scope, retry, citation snapshot badges |
| 2026-10-31 | Frontend Production Build (`npm --prefix frontend run build`) | Exit 0 in 2.03s | TypeScript compile & Vite production build clean |
| 2026-10-31 | Ruff lint & format (`ruff check backend`, `ruff format --check backend`) | Exit 0 | All 61 backend files clean |
| 2026-10-31 | UI/UX Redesign Frontend Vitest (`npm --prefix frontend test -- --run`) | Exit 0 — 30 passed in 3.73s | 7 test files passing; tabs, metrics, views, and navigation verified |
| 2026-10-31 | UI/UX Redesign Production Build (`npm --prefix frontend run build`) | Exit 0 in 2.02s | Clean bundle, 0 errors |
| 2026-10-31 | Backend Post-Redesign Regression Suite (`pytest backend/tests`) | Exit 0 — 100 passed in 34.79s | Zero backend regressions across all 100 tests |
| 2026-10-31 | Ruff format and lint checks (`ruff check backend; ruff format --check backend`) | Exit 0 | All 61 backend files clean |
| 2026-10-31 | Ingestion Lifecycle Suite (`pytest backend/tests/test_ingestion_lifecycle.py`) | Exit 0 — 11 passed in 4.70s | PDF/DOCX limits, corruption, failure status, restart recovery, retry cleanup |
| 2026-10-31 | Full Backend Pytest Suite (`pytest backend/tests`) | Exit 0 — 111 passed in 22.81s | Zero regressions across all 111 tests |
| 2026-10-31 | Full Frontend Vitest Suite (`npm --prefix frontend test -- --run`) | Exit 0 — 33 passed in 3.38s | 8 test files; upload dedup, active polling, error badge rendering |
| 2026-10-31 | Frontend Production Build (`npm --prefix frontend run build`) | Exit 0 in 1.26s | Clean bundle, 0 errors |
| 2026-10-31 | Ruff lint & format (`ruff check backend; ruff format --check backend`) | Exit 0 | All 62 backend files clean |
| 2026-10-31 | Normalization & Structure Chunking Suite (`pytest backend/tests/test_normalize.py`) | Exit 0 — 8 passed in 0.30s | Zero-width stripping, math normalization, sampling theorem benchmark |
| 2026-10-31 | Full Backend Pytest Suite (`pytest backend/tests`) | Exit 0 — 119 passed in 26.84s | Zero regressions across all 14 test suites |
| 2026-10-31 | Full Frontend Vitest Suite (`npm --prefix frontend test -- --run`) | Exit 0 — 33 passed in 57.51s | Clean across all 8 test files |
| 2026-10-31 | Frontend Production Build (`npm --prefix frontend run build`) | Exit 0 in 2.99s | Clean bundle, 0 errors |
| 2026-10-31 | Ruff lint & format (`ruff check backend; ruff format --check backend`) | Exit 0 | All 63 backend files clean |
| 2026-10-31 | Deterministic Evaluation Runner (`python backend/app/evaluation/runner.py`) | Exit 0 | 20 questions, 1.0 abstention, 0.933 recall@5, 1.0 citation rate |
| 2026-10-31 | Retrieval Engine Benchmark (`backend/tests/test_retrieval.py`) | Exit 0 — 9 passed in 0.32s | Exact code identifiers (`clc`, `interp1`), scoped calibration verified |
| 2026-10-31 | Full Backend Pytest Suite (`pytest backend/tests`) | Exit 0 — 120 passed in 67.90s | Zero regressions across all 15 test suites |
| 2026-10-31 | Full Frontend Vitest Suite (`npm --prefix frontend test -- --run`) | Exit 0 — 33 passed in 11.17s | Clean across all 8 test files |
| 2026-10-31 | Frontend Production Build (`npm --prefix frontend run build`) | Exit 0 in 3.21s | Clean bundle, 0 errors |
| 2026-10-31 | Ruff lint & format (`ruff check backend; ruff format --check backend`) | Exit 0 | All 63 backend files clean |
| 2026-10-31 | Intent Classification Suite (`pytest backend/tests/test_intent.py`) | Exit 0 — 53 passed in 0.10s | 9 query intent categories verified |
| 2026-10-31 | Phase 4 Intents & Scope Suite (`pytest backend/tests/test_phase4_intents_and_scope.py`) | Exit 0 — 11 passed in 0.69s | Verbatim raw delivery, conversation recaps, prompt directives, BUG-04 fix |
| 2026-10-31 | Full Backend Pytest Suite (`pytest backend/tests`) | Exit 0 — 162 passed in 153.42s | Zero regressions across all 16 test suites |
| 2026-10-31 | Full Frontend Vitest Suite (`npm --prefix frontend test -- --run`) | Exit 0 — 33 passed in 14.93s | Clean across all 8 test files |
| 2026-10-31 | Frontend Production Build (`npm --prefix frontend run build`) | Exit 0 in 1.88s | Production bundle clean |
| 2026-10-31 | Ruff lint & format (`ruff check backend; ruff format --check backend`) | Exit 0 | All 64 backend files clean |
| 2026-10-31 | Deterministic Evaluation Runner (`python backend/app/evaluation/runner.py`) | Exit 0 | 20 questions, 1.0 abstention, 1.0 citation validity, 0.933 recall@5 |
| 2026-10-31 | Grounded Generation Suite (`pytest backend/tests/test_grounded_generation.py`) | Exit 0 — 7 passed in 0.03s | Contradiction suppression, prefix matching, schema normalization verified |
| 2026-10-31 | Full Backend Pytest Suite (`pytest backend/tests`) | Exit 0 — 171 passed in 23.75s | Zero regressions across all 17 backend test suites |
| 2026-10-31 | Full Frontend Vitest Suite (`npm --prefix frontend test -- --run`) | Exit 0 — 33 passed in 5.09s | Clean across all 8 frontend test files |
| 2026-10-31 | Frontend Production Build (`npm --prefix frontend run build`) | Exit 0 in 1.46s | Production bundle clean |
| 2026-10-31 | Ruff lint & format (`ruff check backend; ruff format --check backend`) | Exit 0 | All 65 backend files clean |
| 2026-10-31 | Mathematical Reasoning Suite (`pytest backend/tests/test_math_reasoning.py`) | Exit 0 — 11 passed in 0.06s | Nyquist rate, interval, 1001/21 counts, 8 Hz aliasing, code semantics |
| 2026-10-31 | Full Backend Pytest Suite (`pytest backend/tests`) | Exit 0 — 182 passed in 29.53s | Zero regressions across all 18 backend test suites |
| 2026-10-31 | Full Frontend Vitest Suite (`npm --prefix frontend test -- --run`) | Exit 0 — 33 passed in 5.86s | Clean across all 8 frontend test files |
| 2026-10-31 | Frontend Production Build (`npm --prefix frontend run build`) | Exit 0 in 4.14s | Production bundle clean in 4.14s |
| 2026-10-31 | Ruff lint & format (`ruff check backend; ruff format --check backend`) | Exit 0 | All 67 backend files clean |
| 2026-10-31 | API Reliability Suite (`pytest backend/tests/test_api_reliability.py`) | Exit 0 — 8 passed in 6.01s | Envelopes, 502 recovery, 409 conflict, stale turns, idempotency |
| 2026-10-31 | Full Backend Pytest Suite (`pytest backend/tests`) | Exit 0 — 190 passed in 68.19s | Zero regressions across all 20 test suites, 0 warnings |
| 2026-10-31 | Full Frontend Vitest Suite (`npm --prefix frontend test -- --run`) | Exit 0 — 36 passed in 14.34s | Clean across all 9 test files including ErrorBoundary |
| 2026-10-31 | Frontend Production Build (`npm --prefix frontend run build`) | Exit 0 in 1.82s | Production bundle clean |
| 2026-10-31 | Ruff lint & format (`ruff check backend; ruff format --check backend`) | Exit 0 | All 68 backend files clean |
| 2026-10-31 | Full Frontend Vitest Suite (`npm --prefix frontend test -- --run`) | Exit 0 — 36 passed in 4.25s | Evidence transparency, views, and navigation verified |
| 2026-10-31 | Frontend Production Build (`npm --prefix frontend run build`) | Exit 0 in 1.73s | Production bundle clean, zero `any` types in source |
| 2026-10-31 | Full Backend Pytest Suite (`pytest backend/tests`) | Exit 0 — 194 passed in 24.90s | Zero regressions across all 20 test files |
| 2026-10-31 | Ruff lint & format (`ruff check backend; ruff format --check backend`) | Exit 0 | All 68 backend files clean |
| 2026-10-31 | Conversation Persistence Suite (`pytest backend/tests/test_conversations.py`) | Exit 0 — 10 passed in 12.82s | Scoped context, 3-turn bound, cascade delete verified |
| 2026-10-31 | Full Backend Pytest Suite (`pytest backend/tests`) | Exit 0 — 194 passed in 24.90s | Zero regressions across all 20 backend test files |
| 2026-10-31 | Full Frontend Vitest Suite (`npm --prefix frontend test -- --run`) | Exit 0 — 36 passed in 4.34s | Clean across all 9 frontend test files |
| 2026-10-31 | Frontend Production Build (`npm --prefix frontend run build`) | Exit 0 in 1.48s | Production bundle clean |
| 2026-10-31 | Ruff lint & format (`ruff check backend; ruff format --check backend`) | Exit 0 | All 68 backend files clean |
| 2026-10-31 | Full Frontend Vitest Suite (`npm --prefix frontend test -- --run`) | Exit 0 — 36 passed in 4.25s | Evidence transparency, views, and navigation verified |
| 2026-10-31 | Frontend Production Build (`npm --prefix frontend run build`) | Exit 0 in 1.73s | Production bundle clean, zero `any` types in source |
| 2026-10-31 | Full Backend Pytest Suite (`pytest backend/tests`) | Exit 0 — 194 passed in 24.90s | Zero regressions across all 20 test files |
| 2026-10-31 | Ruff lint & format (`ruff check backend; ruff format --check backend`) | Exit 0 | All 68 backend files clean |
