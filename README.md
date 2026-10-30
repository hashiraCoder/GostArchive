# GhostArchive

> **A local-first, evidence-grounded AI archive for your personal documents.**

GhostArchive helps you rediscover what your own collection of notes, letters, journals, and documents says — by meaning, not just keywords. You ask a question, and the app retrieves the original passages that support the answer, so you can verify every claim against the source text.

**The "ghost" is the trace left by words that survived their author or moment** — this is a tool for preservation and discovery, not simulation or impersonation.

---

## Status

> ⚠️ **This project is in active development.** The checklist in `docs/PHASE_CHECKLIST.md` tracks what is actually done.

### What is implemented

- [x] Repository foundations and project documentation (Phase 0)
- [x] Backend skeleton and health check (Phase 1)
- [x] Document ingestion and SQLite persistence (Phase 2)
- [x] Embeddings and semantic search (Phase 3)
- [x] Grounded Q&A with citation validation (Phase 4)
- [x] Evidence UI and product polish (Phase 5)
- [x] Test suite and evaluation runner (Phase 6)
- [ ] README, demo, submission (Phase 7)

---

## What this is (and is not)

**GhostArchive does:**
- Import `.txt` and `.md` files entirely locally — nothing leaves your machine.
- Index them using a local embedding model (Sentence Transformers).
- Search by meaning with passages ranked by relevance.
- Answer questions through `POST /api/chat` using a local Ollama model grounded in retrieved evidence.
- Show trusted source metadata and the exact retrieved passage behind every citation.
- Manage the local archive through the React UI, including import, semantic search, grounded questions, citation inspection, and confirmed deletion.
- Tell you honestly when your archive does not contain an answer.

**GhostArchive does NOT:**
- Simulate, impersonate, or claim to contact any person, living or deceased.
- Invent facts, dates, quotes, or relationships not found in your documents.
- Send your documents, questions, or embeddings to any cloud service.
- Guarantee hallucination-free answers — it validates citations against retrieved passages, but semantic support requires human review.
- Support scanned PDF images, audio, or face recognition.

---

## Prerequisites

Before you begin, install the following on your Windows machine:

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ (3.12 preferred) | Backend runtime |
| Node.js | 18 LTS or 20 LTS | Frontend build |
| [Ollama](https://ollama.com/) | Latest | Local language model serving |
| Git | Any | Source control |

> **Disk space:** The default embedding model (`all-MiniLM-L6-v2`, ~90 MB) downloads on first run. The default generation model (`gemma3:1b`, ~800 MB) must be pulled via `ollama pull gemma3:1b`. These are one-time setup downloads; after that, the app runs offline.

---

## Setup (Windows)

> These steps will be verified and updated in Phase 7 after the full MVP is complete. Do not follow them until Phase 7 is checked off in `docs/PHASE_CHECKLIST.md`.

```powershell
# 1. Clone the repository
git clone https://github.com/your-username/GhostArchive.git
cd GhostArchive

# 2. Set up the Python backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. Configure environment
copy ..\env.example .env
# Edit .env if your Ollama port or model differs

# 4. Pull the local language model (requires internet, one-time)
ollama pull gemma3:1b
# The embedding model downloads automatically on first backend start

# 5. Start the backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 6. In a new terminal, set up and start the frontend
cd ..\frontend
npm install
npm run dev
# Open http://localhost:5173
```

---

## Privacy and data handling

- All imported files, extracted text, embeddings, and chat questions are stored **only on your local machine** in `backend/data/` (excluded from git by `.gitignore`).
- The embedding model is downloaded from Hugging Face on first use. After that, the app works offline.
- `gemma3:1b` is served locally by Ollama; no text is sent to Google or any third party during runtime.
- Logs contain only IDs, sizes, durations, and error codes — never document content.
- Deleting a document removes the stored file, metadata, chunks, and index vectors.

> **Note:** We do not claim "encrypted at rest" unless encryption is implemented and tested. Runtime data is local but not encrypted by default.

---

## Known limitations

> This section will be updated in Phase 7 with verified, measured limitations.

- Only `.txt` and `.md` files are supported in the MVP.
- The app is single-user; no access controls.
- Semantic search quality depends on the embedding model and chunking strategy; it has not been benchmarked on all document types.
- The language model (`gemma3:1b`) is small and may produce incomplete answers; it is grounded by citation validation, not factuality guarantees.
- Ollama must be running locally for answer generation; search and document management remain available when it is offline.
- First-time setup requires an internet connection to download the models.

---

## Running tests

The backend and frontend suites, plus the deterministic offline evaluation runner, are verified.

```powershell
# Backend tests
cd backend
pytest --tb=short

# Frontend tests
cd frontend
npm run test

# Deterministic corpus evaluation
cd ..\backend
.\venv\Scripts\python.exe -m app.evaluation.runner --questions ..\data\evaluation\questions.json --corpus ..\data\sample_archive
```

---

## Sample archive

`data/sample_archive/` contains synthetic fictional documents used for development and evaluation. They are not real personal records. See `docs/EVALUATION_RESULTS.md` (created in Phase 7) for benchmark results.

---

## License

> License choice is pending (see `docs/DECISIONS.md`). Dependency and model licenses:
> - Sentence Transformers `all-MiniLM-L6-v2`: Apache-2.0
> - `gemma3:1b` via Ollama: [Gemma Terms of Use](https://ai.google.dev/gemma/terms) (open-weight, not OSI-approved open source)
> - ChromaDB: Apache-2.0
> - FastAPI: MIT
> - React, Vite, Tailwind CSS: MIT

---

## Attribution

Built with [Ollama](https://ollama.com/), [Sentence Transformers](https://www.sbert.net/), [ChromaDB](https://www.trychroma.com/), [FastAPI](https://fastapi.tiangolo.com/), [React](https://react.dev/), [Vite](https://vitejs.dev/), and [Tailwind CSS](https://tailwindcss.com/).

---

## Contributing

This project is in active MVP development. See `AGENTS.md` for engineering rules. Open an issue before submitting a pull request.
