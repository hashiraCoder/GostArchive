# Architecture Decisions Log

> Append-only. Do not rewrite or delete entries to disguise a change. If a decision is reversed, add a new entry explaining what changed and why.

---

## D-01 — Python version: 3.11+ (prefer 3.12)

**Date:** 2026-10-29  
**Status:** Decided  
**Decision:** Use Python 3.11 as the minimum requirement; use 3.12 if all key dependencies (FastAPI, pydantic, chromadb, sentence-transformers, PyMuPDF) support it at the time of initial install.  
**Rationale:** Spec (`PROJECT.md`) says "Python 3.11+ (prefer 3.12 if all dependencies support it)." Sentence Transformers and ChromaDB both support 3.12 as of late 2026. Pin exact version in requirements lock after first successful install.

---

## D-02 — SQLite is the authoritative store; ChromaDB is a rebuildable index

**Date:** 2026-10-29  
**Status:** Decided  
**Decision:** SQLite holds document metadata, chunk text, source offsets, and processing state. ChromaDB holds only vectors and references to SQLite IDs. All citation resolution goes through SQLite. ChromaDB can be wiped and rebuilt from SQLite chunks.  
**Rationale:** Prevents the vector index from becoming the only copy of content metadata. Enables recovery from index corruption without data loss. Required by `ARCHITECTURE.md §7` and `TECH_STACK.md`.

---

## D-03 — API bound to 127.0.0.1; CORS allows loopback Vite origin only

**Date:** 2026-10-29  
**Status:** Decided  
**Decision:** FastAPI binds to `127.0.0.1:8000`. CORS `allow_origins` contains only `http://localhost:5173` and `http://127.0.0.1:5173`. No wildcard origins.  
**Rationale:** Local-first privacy requirement (`AGENTS.md §Local-first privacy`). The API must not be reachable from external hosts or browsers on other machines.

---

## D-04 — No cross-store transactions; use explicit state machine and compensation

**Date:** 2026-10-29  
**Status:** Decided  
**Decision:** SQLite and ChromaDB do not share a transaction. The document lifecycle uses explicit states: `processing → ready | failed` for imports, `deleting` for deletions. Each step implements idempotent cleanup.  
**Rationale:** `DATABASE_DESIGN.md §4` and `DATA_LIFECYCLE.md` both require this. Pretending cross-store atomicity exists would create silent data inconsistencies.

---

## D-05 — Sample archive uses synthetic fictional content only

**Date:** 2026-10-29  
**Status:** Decided  
**Decision:** The `data/sample_archive/` evaluation set contains entirely fictional characters, places, and events. No real personal names, real addresses, real historical individuals, or real documents are included.  
**Rationale:** Privacy (`AGENTS.md §Local-first privacy`), safety (not impersonating real people), and reproducibility (synthetic data can be committed to the repo without privacy concerns).

---

## D-06 — top_k default 5, hard cap 8; no distance threshold until calibrated

**Date:** 2026-10-29  
**Status:** Decided  
**Decision:** `RETRIEVAL_TOP_K` defaults to 5 and is clamped to a maximum of 8. No similarity distance threshold is applied until measured against the evaluation set.  
**Rationale:** `AGENTS.md §RAG and evidence rules` prohibits introducing a threshold without calibration. `RAG_DESIGN.md §3` specifies these defaults. A raw distance value is not a calibrated confidence.

---

## D-07 — Project license

**Date:** 2026-10-29  
**Status:** OPEN — awaiting user decision  
**Options:** MIT, Apache-2.0, or other  
**Constraints:**  
- Must be compatible with: Apache-2.0 (ChromaDB, Sentence Transformers), MIT (FastAPI, React, Vite, Tailwind).  
- `gemma3:1b` is under Gemma Terms of Use — not an OSI license; project license does not cover the model.  
**Action required:** User must choose a license before Phase 7.

---

## D-08 — Node.js version for frontend

**Date:** 2026-10-29  
**Status:** Assumed 20 LTS; confirm with user  
**Decision:** Using Node.js 20 LTS for frontend toolchain. Vite 5+ and pnpm/npm current versions support it.  
**Action required:** Confirm or override before Phase 1 frontend setup.
