# Configuration Guide

GhostArchive reads all runtime configuration from environment variables or a root `.env` file via `pydantic-settings`. All settings use the prefix `GHOSTARCHIVE_` when specified via environment variables, or their exact field names in `.env`.

---

## 1. Environment Variables Reference

| Variable | Default Value | Description & Constraints |
| :--- | :--- | :--- |
| `GHOSTARCHIVE_HOST` | `127.0.0.1` | Network interface for FastAPI backend. **Must remain `127.0.0.1`** for local privacy. Never set to `0.0.0.0`. |
| `GHOSTARCHIVE_PORT` | `8000` | TCP port for FastAPI backend. |
| `GHOSTARCHIVE_DATA_DIR` | `backend/data` | Path to persistent storage. Stores SQLite `ghostarchive.db`, uploaded text files in `files/`, and vector database in `chroma_store/`. Excluded from Git. |
| `UPLOAD_MAX_BYTES` | `5242880` (5 MiB) | Maximum allowed file upload size. Uploads exceeding this threshold return HTTP 413. |
| `EXTRACTED_TEXT_MAX_CHARS` | `500000` | Maximum plain text characters per document. Prevents memory exhaustion attacks. |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Loopback address for the local Ollama daemon. |
| `OLLAMA_MODEL` | `gemma3:1b` | Ollama model identifier used for evidence-grounded generation. First use requires `ollama pull <model>`. |
| `OLLAMA_TIMEOUT_SECONDS` | `60` | Generation request timeout in seconds. |
| `GHOSTARCHIVE_LLM_PROVIDER` | `ollama` | Generation provider: `ollama` (default) or `external`. |
| `GHOSTARCHIVE_EXTERNAL_API_KEY` | *(None)* | Optional API key for external OpenAI-compatible service. Strictly required only if `llm_provider` is set to `external`. |
| `GHOSTARCHIVE_EXTERNAL_MODEL` | `gemini-2.5-flash` | Model identifier used if external provider is active. |
| `GHOSTARCHIVE_EXTERNAL_API_BASE_URL` | *(None)* | Custom base URL for external OpenAI-compatible provider (defaults to `https://api.openai.com/v1`). |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model identifier. Downloaded on first run from Hugging Face (~90 MB) and cached locally. |
| `RETRIEVAL_TOP_K` | `5` | Default number of passages retrieved per question (clamped to 1–8). |
| `RETRIEVAL_TOP_K_MAX` | `8` | Maximum upper limit for retrieved passages. |
| `RETRIEVAL_MIN_SIMILARITY` | `0.30` | Calibrated cosine similarity threshold. Candidates below this threshold are rejected unless rescued by rank-0 lexical match. |
| `RETRIEVAL_LEXICAL_BOOST` | `true` | Enables FTS5 BM25 hybrid ranking fusion with dense vector results. |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated list of origins allowed by CORS. Must match your Vite frontend. |
| `LOG_LEVEL` | `INFO` | Logging verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |

---

## 2. Directory Structure of Runtime Data

When GhostArchive runs, it automatically manages the data directory configured by `GHOSTARCHIVE_DATA_DIR`:

```text
backend/data/
├── chroma_store/             # ChromaDB persistent index (HNSW cosine space)
├── files/                    # Stored user documents (saved with UUIDv4 filenames)
│   ├── 4b0f-9b6c-....txt
│   └── 7fd6-71b7-....md
└── ghostarchive.db           # SQLite database (documents, chunks, FTS5 index, conversations)
```

> **Important Privacy Notice:** The entire `backend/data/` folder is excluded by `.gitignore`. Never commit or publish files from this directory to a public repository.

---

## 3. Switching LLM Providers

### Default Mode: Local Ollama (100% Offline)
```ini
GHOSTARCHIVE_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=gemma3:1b
```
In this mode, zero network requests leave your machine during answer generation.

### Optional Mode: External Provider (Cloud Opt-in)
If local hardware is severely constrained and you explicitly choose to use a remote cloud API, configure:
```ini
GHOSTARCHIVE_LLM_PROVIDER=external
GHOSTARCHIVE_EXTERNAL_API_KEY=your-api-key-here
GHOSTARCHIVE_EXTERNAL_MODEL=gemini-2.5-flash
GHOSTARCHIVE_EXTERNAL_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```
> **Note:** If `GHOSTARCHIVE_LLM_PROVIDER=external` is selected but `GHOSTARCHIVE_EXTERNAL_API_KEY` is left blank, GhostArchive safely falls back to local Ollama with a warning.
