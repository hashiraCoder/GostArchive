# GhostArchive — Project Memory

> Durable implementation facts. Updated only after a phase is verified (real commands run, real output confirmed). Do not store planned state as done. Do not duplicate specs. Separate planned / implemented / tested states clearly.

## Repository identity

- **Project name:** GhostArchive
- **Repository path:** `d:\main_projects\GostArchive`
- **Primary branch:** `main`
- **Language/runtime:** Python 3.11+, TypeScript (Node 18/20 LTS)
- **Stack settled:** FastAPI + SQLite + ChromaDB + SentenceTransformers + Ollama + React/Vite/Tailwind

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

### Phase 1–10
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
| D-06 | `top_k` default 5, hard cap 8; no similarity threshold until calibrated |

## Open decisions (user input needed)

| # | Question | Default assumed | Notes |
|---|---|---|---|
| D-07 | Project license | TBD | Must be compatible with all deps |
| D-08 | Node.js version | 20 LTS | Used for frontend |

## Known issues

None recorded yet. Create `docs/KNOWN_ISSUES.md` when the first real verified issue is discovered.

## Verified command log

| Date | Command | Result | Notes |
|---|---|---|---|
| 2026-10-29 | Initial repo inspection | Fresh repo, only `ai_md/` present | No commits yet |
| 2026-10-29 | `git check-ignore` on 7 patterns | All 6 sensitive patterns correctly blocked; sample archive not blocked | `.gitignore` verified |
| 2026-10-29 12:22 | `git commit 5749358` | 35 files, 2363 insertions, exit 0 | Phase 0 complete |
