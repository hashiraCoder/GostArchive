# Troubleshooting & Frequently Asked Questions

This document covers common setup issues, diagnostic commands, and recovery procedures for GhostArchive.

---

## 1. System Readiness Diagnostics

Before debugging specific errors, check the health of all subsystems by visiting:
- **Liveness:** `http://127.0.0.1:8000/api/health`
- **Readiness:** `http://127.0.0.1:8000/api/ready?check_inference=true`

The UI also provides a live inspection panel under the **System Status** tab.

---

## 2. Common Issues & Solutions

### Issue 1: "Local Ollama service unreachable" (Status: Unavailable / Degraded)
- **Symptom:** The status pill shows Degraded/Unavailable, and asking questions fails with `MODEL_UNAVAILABLE`.
- **Root Cause:** The Ollama daemon is not running on `127.0.0.1:11434`.
- **Solution:**
  1. Open a new terminal and run:
     ```bash
     ollama serve
     ```
  2. Verify it is reachable:
     ```bash
     curl http://127.0.0.1:11434/api/tags
     ```
  3. Reload the GhostArchive web page.

### Issue 2: "Configured model 'gemma3:1b' is not installed in local Ollama" (Error: MODEL_NOT_FOUND)
- **Symptom:** Ollama is running, but asking questions fails with `MODEL_NOT_FOUND`.
- **Root Cause:** The model weights have not been downloaded to your Ollama library.
- **Solution:**
  1. In your terminal, pull the model:
     ```bash
     ollama pull gemma3:1b
     ```
  2. Verify the model appears in your local tags:
     ```bash
     ollama list
     ```

### Issue 3: "Cannot reach local GhostArchive service at 127.0.0.1:8000" (Error: SERVICE_UNREACHABLE)
- **Symptom:** The browser displays a 503 error banner in the frontend.
- **Root Cause:** The FastAPI backend server is not running, or crashed during startup.
- **Solution:**
  1. Check the backend terminal for Python exceptions or missing dependencies.
  2. Start the backend:
     ```powershell
     cd backend
     .\venv\Scripts\Activate.ps1
     uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
     ```

### Issue 4: "File upload rejected: Only .txt and .md files are supported" (Error: VALIDATION_ERROR / 422)
- **Symptom:** Dragging a PDF, DOCX, or CSV file fails with HTTP 422.
- **Root Cause:** GhostArchive 0.1.0 natively ingests plain text (`.txt`) and Markdown (`.md`) documents.
- **Solution:**
  1. Convert your PDF or Word document to Markdown or plain text using Pandoc, pdftotext, or an editor.
  2. Upload the resulting `.md` or `.txt` file.

### Issue 5: Incomplete or Interrupted Indexing on Startup
- **Symptom:** Server power was cut mid-upload, leaving a file stuck in `processing`.
- **Root Cause:** Ingestion process was terminated abruptly before transaction commit.
- **Solution:**
  - GhostArchive includes automatic startup recovery. On application boot, `recover_interrupted_documents(settings)` inspects SQLite for any documents in `processing` or `deleting` and safely marks them `failed`, allowing you to delete or re-upload them cleanly.

---

## 3. Maintenance & Recovery Utilities

### Rebuilding the ChromaDB Vector Index from SQLite
Because SQLite is the authoritative source of truth, the entire ChromaDB vector index can be wiped and reconstructed from SQLite chunks without losing any text or metadata:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -c "from app.core.config import get_settings; from app.services.index_service import rebuild_vector_index; rebuild_vector_index(get_settings())"
```

---

## 4. Frequently Asked Questions (FAQ)

### Q: Can GhostArchive run with no internet connection at all?
**Yes.** Once you have completed the initial setup (installing Python/Node dependencies, running `ollama pull gemma3:1b`, and allowing Sentence Transformers to download `all-MiniLM-L6-v2` once), GhostArchive operates completely offline without internet connectivity.

### Q: Are my documents encrypted on disk?
Runtime documents in `backend/data/` are stored in plain text and SQLite/Chroma binary format in your user directory. They are protected by your operating system user account permissions. We recommend using OS-level disk encryption (e.g. BitLocker on Windows, FileVault on macOS, or LUKS on Linux).

### Q: What should I do if an answer says "Insufficient Evidence"?
GhostArchive is specifically designed to tell you honestly when evidence is absent rather than hallucinating plausible-sounding falsehoods. If you receive an insufficient evidence response:
1. Check that the relevant document has been uploaded.
2. In the **Ask Archive** view, select **Entire Archive** instead of scoping to a single document.
3. Try rephrasing your question using descriptive vocabulary present in your source documents.
