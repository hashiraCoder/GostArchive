# Technology Stack and Ownership

## Stack is intentionally fixed for the MVP

| Layer | Selected technology | Owns | Do not add without a reason |
|---|---|---|---|
| UI | React + Vite + TypeScript | User journeys, display state, accessible controls | Redux/Zustand for simple state, heavy design framework |
| Styling | Tailwind CSS + project CSS tokens | Responsive layout, theme, spacing, typography | Multiple competing styling systems |
| HTTP client | One typed API client built on `fetch` | Base URL, JSON parsing, error mapping, request types | Scattered `fetch` calls inside every component |
| Backend API | FastAPI | HTTP routes, dependency wiring, validation, error envelopes | Second backend framework |
| API/data schemas | Pydantic v2 | Request/response validation, internal settings | Untyped dicts at public boundaries |
| Config | pydantic-settings / environment | Ports, data directory, limits, model IDs | Hardcoded environment-specific values |
| Local LLM | Ollama HTTP API | Local generation only | Hosted model API or hidden cloud fallback |
| Embeddings | Sentence Transformers | Document and query vectors, loaded once per process | Re-embedding whole archive on every query |
| Vector index | ChromaDB persistent client | Similarity retrieval and vector persistence | Remote vector service |
| Authoritative data | SQLite | Document metadata, extracted text/chunks, source offsets, state | Treating vector metadata as authoritative |
| Extraction | Python standard library for txt/md; PyMuPDF optional | Validate and extract supported content | OCR, arbitrary office formats in MVP |
| Backend tests | pytest + FastAPI TestClient/httpx | Unit, API, integration, evaluation | Tests that depend on live internet/model where mocks suffice |
| Frontend tests | Vitest + React Testing Library (where included) | User-visible states and core interactions | Snapshot-only confidence |
| Formatting | Ruff for Python; ESLint/Prettier for TS | Consistent formatting/lint | Failing to run checks before claiming completion |

## Model configuration

- Generation default: `gemma3:1b` using Ollama; configurable by `OLLAMA_MODEL`.
- Embedding default: `sentence-transformers/all-MiniLM-L6-v2`; configurable by `EMBEDDING_MODEL`.
- Never hardcode a model identifier in business logic; read validated settings.
- First-time download may need internet. README must distinguish setup-time downloads from offline runtime.
- Check model terms and third-party licenses before publishing. “Open-weight” does not automatically mean OSI-approved open-source.
- For the target Windows laptop (8 GB RAM, RTX 2050 4 GB VRAM), test context length, startup, indexing latency, and generation latency. A model's download size is not its total runtime memory.

## Data ownership and authority

- SQLite is authoritative for document metadata, chunk text, source offsets/page, and processing state.
- ChromaDB contains vectors and stable references to SQLite records; it can be rebuilt from SQLite.
- Original imported bytes are stored under an app-owned private data directory with generated filenames.
- The frontend receives public display metadata only; never return absolute local storage paths.

## Versioning policy

Use a committed frontend lockfile and pinned backend dependencies (requirements lock or equivalent) once installation has succeeded. State tested versions in README. Do not invent versions before installation or silently upgrade dependencies during a feature task.
