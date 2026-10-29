# Phase Checklist and Verified State

> Only mark an item complete after personally running the relevant command/test or inspecting the actual implementation. Planning documents do not count as implementation. Mirrors `ai_md/PHASE_CHECKLIST.md`; this file is the working progress ledger.

## Current state

- [x] Phase 0 — Repository foundations ✅ `5749358` (2026-10-29)
- [ ] Phase 1 — Frontend/backend skeleton and health check
- [ ] Phase 2 — Document ingestion and SQLite persistence
- [ ] Phase 3 — Embeddings, Chroma persistence, semantic search
- [ ] Phase 4 — Ollama, grounded RAG, citation validation
- [ ] Phase 5 — Evidence UI and product polish
- [ ] Phase 6 — Unit/integration/evaluation tests
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

### Sample archive documents created

| File | Evaluation purpose |
|---|---|
| `data/sample_archive/letters/letter_to_eliza_1887.txt` | Answerable factual question |
| `data/sample_archive/letters/letter_from_the_front_1944.txt` | Multi-chunk evidence, dates, names |
| `data/sample_archive/journals/spring_journal_1923.md` | Paraphrased retrieval |
| `data/sample_archive/journals/winter_journal_1923.md` | Date/name references |
| `data/sample_archive/notes/botanical_notes.md` | Exact term/name search |
| `data/sample_archive/notes/unanswerable_subject.txt` | Questions that archive cannot answer |
| `data/sample_archive/injection/adversarial_document.txt` | Prompt injection test |
| `data/sample_archive/notes/conflicting_accounts.txt` | Contradictory statements |

---

## Phase 1 — Frontend/Backend Skeleton

### Acceptance gates

- [ ] `GET /api/health` returns `{"status":"ok","app_version":"0.1.0"}`
- [ ] `GET /api/ready` returns per-dependency map; no crash when Ollama absent
- [ ] pytest `tests/test_health.py` passes (all tests, zero failures)
- [ ] React app loads at `http://localhost:5173` and shows status indicator
- [ ] StatusIndicator renders `ready/degraded/unavailable` states correctly

---

## Phase 2 — Document Ingestion

### Acceptance gates

- [ ] `POST /api/documents` with valid `.txt` → `status: ready` in DB
- [ ] `POST /api/documents` with invalid extension → 422
- [ ] `POST /api/documents` with oversized file → 413/422
- [ ] Duplicate content (same SHA-256) → documented behavior
- [ ] `GET /api/documents` returns list
- [ ] `DELETE /api/documents/{id}` removes SQLite row
- [ ] pytest ingestion tests pass

---

## Phase 3 — Embeddings and Search

### Acceptance gates

- [ ] Import sample doc → semantic search paraphrase → ≥1 hit in top-5
- [ ] Search with no documents → empty result (not error)
- [ ] Index persists across backend restart
- [ ] pytest retrieval tests pass

---

## Phase 4 — Grounded Q&A

### Acceptance gates

- [ ] Answerable question → answer + resolved citation (SQLite source, not model text)
- [ ] Unanswerable question → `insufficient_evidence: true`, no fabricated answer
- [ ] Ollama unavailable → `MODEL_UNAVAILABLE` error; search still works
- [ ] Hallucinated citation ID dropped
- [ ] Injection document: answer does not follow injected instruction
- [ ] pytest chat tests pass (with mocked Ollama)

---

## Phase 5 — Evidence UI

### Acceptance gates

- [ ] End-to-end manual: import → search → ask → inspect citation → delete → restart → state persists
- [ ] All UI states implemented: empty, loading, error, insufficient evidence, model offline
- [ ] Delete flow: confirmation → deleting → success or retry-error

---

## Phase 6 — Tests and Evaluation

### Acceptance gates

- [ ] `pytest --tb=short` exits 0
- [ ] Evaluation runner produces real metric output (numbers, dataset size, model stated)
- [ ] All 7 evaluation categories represented in `data/evaluation/questions.json`

---

## Phase 7 — README and Demo

### Acceptance gates

- [ ] Fresh-checkout setup on Windows following README steps reaches working demo
- [ ] `docs/EVALUATION_RESULTS.md` contains real measured metrics
- [ ] `LICENSE` file present with verified compatible license

---

## Known blockers

- None recorded yet; this means not yet assessed, not that no blockers exist.
- Open user decisions: project license (D-07), Node.js version confirmation (D-08).

---

## Update format for coding agents

For each completed phase, add:
- Commit/hash if known.
- Commands actually run and exit result.
- Tests passed/failed/skipped.
- Features implemented and important limitations.
- Remaining blockers and next single task.
