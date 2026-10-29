# Architecture

## 1. Topology

```text
Browser (React/Vite on 127.0.0.1:5173)
          |
          | JSON/HTTP; local-only CORS
          v
FastAPI (127.0.0.1:8000)
  |-- API/router + Pydantic contracts
  |-- ingestion service --> parser --> normalizer --> chunker
  |                                          |              |
  |                                          v              v
  |                                    SQLite source     SentenceTransformer
  |                                    metadata/chunks   embeddings
  |                                                          |
  |                                                          v
  |                                                    Chroma persistent index
  |
  |-- query service --> retrieve top-k --> prompt composer --> Ollama
  |                                                 (127.0.0.1:11434)
  |                                                            |
  |<---------------- structured model output ------------------|
  |-- validate schema + citation IDs --> resolve citations from SQLite
          |
          v
Browser displays answer + source excerpts
```

## 2. Runtime boundaries

- Frontend owns presentation and user actions only.
- FastAPI coordinates validation and service calls.
- SQLite is the authoritative source for document/chunk metadata and source text.
- Chroma is a local index, rebuildable from SQLite chunks if necessary.
- Embedding provider and LLM provider sit behind small interfaces to permit swapping models without changing endpoint contracts.
- Ollama is called at `OLLAMA_BASE_URL`; the default is a loopback URL.
- No cloud services are part of MVP.

## 3. Proposed backend modules

```text
backend/app/
  main.py
  core/config.py
  core/errors.py
  api/routes/health.py
  api/routes/documents.py
  api/routes/search.py
  api/routes/chat.py
  schemas/documents.py
  schemas/search.py
  schemas/chat.py
  database/connection.py
  database/schema.sql
  database/repositories/documents.py
  database/repositories/chunks.py
  ingestion/file_validation.py
  ingestion/extractors/text.py
  ingestion/extractors/markdown.py
  ingestion/extractors/pdf.py      # optional after MVP text/md
  ingestion/normalize.py
  ingestion/chunking.py
  retrieval/embeddings.py
  retrieval/vector_store.py
  services/document_service.py
  services/search_service.py
  services/chat_service.py
  generation/ollama_client.py
  generation/prompts.py
  generation/output_validation.py
  evaluation/runner.py
```

Do not create empty modules for every path at project start. Add a module when its phase begins. Keep initial code simple.

## 4. Proposed frontend modules

```text
frontend/src/
  app/
    App.tsx
  api/
    client.ts
    documents.ts
    search.ts
    chat.ts
  components/
    AppShell.tsx
    StatusIndicator.tsx
    EmptyState.tsx
    ErrorBanner.tsx
    CitationCard.tsx
  features/
    archive/ArchivePage.tsx
    archive/UploadDropzone.tsx
    chat/MemoryChatPage.tsx
    search/SearchResults.tsx
    source/SourceDrawer.tsx
  styles/
    tokens.css
    global.css
```

Use simple routing or a small router. Do not install a large state-management package unless needed. Keep the API client centralized.

## 5. Request path for an answer

1. Frontend posts question plus optional selected document IDs.
2. API validates length and document filter.
3. Search service embeds the query locally and retrieves top-k chunks.
4. If there is no usable evidence, return an explicit insufficient-evidence response without calling the LLM where appropriate.
5. Prompt composer identifies source IDs and labels document text as untrusted quoted context.
6. Ollama receives a short context, low/moderate temperature, and a structured-output instruction.
7. Pydantic validation checks the model payload.
8. Backend drops/rejects citation IDs not in the retrieved ID set and resolves trusted source details from SQLite.
9. Frontend renders answer and source cards. It must not trust model-generated source paths or citations.

## 6. Failure behavior

- Ollama unavailable/model missing: return a clear readiness/error response; search still works.
- Embedding model unavailable: report model initialization error; don't fake semantic search.
- Parser failure: mark document failed with a safe message; no partial “ready” state.
- Chroma/SQLite inconsistency: log a redacted internal error, preserve recoverability, expose an actionable user message.
- Generation timeout or invalid output: return a retryable error or an explicit insufficient-evidence response; never a canned answer.

## 7. Rebuild strategy

SQLite holds source chunks. Provide an internal/admin CLI or documented maintenance function to recreate Chroma vectors from stored chunks. This prevents an index backup from becoming the only copy of content metadata.
