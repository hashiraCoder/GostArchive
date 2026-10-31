# Backend Architecture & Service Layer

The GhostArchive backend is built with FastAPI, SQLite 3, ChromaDB, Sentence Transformers, and Ollama. It follows a modular service-oriented design.

---

## 1. Directory Structure

```text
backend/app/
├── main.py                     # Application factory, lifespan, CORS, and middleware
├── api/
│   ├── router.py               # Root router mounting sub-routes
│   └── routes/
│       ├── chat.py             # Grounded Q&A (POST /api/chat)
│       ├── conversations.py    # Conversation CRUD (/api/conversations)
│       ├── documents.py        # Ingestion, listing, deletion (/api/documents)
│       ├── health.py           # Health checks (/api/health, /api/ready)
│       ├── search.py           # Hybrid search (POST /api/search)
│       └── summary.py          # Summarization (POST /api/summarize)
├── core/
│   ├── config.py               # Pydantic BaseSettings, path derivation
│   └── errors.py               # Standardized ErrorEnvelope, ErrorCode, handlers
├── database/
│   ├── connection.py           # SQLite connection factory & DDL initialization
│   └── repositories/
│       ├── conversations.py    # Threads, turns, idempotency, bounded history context
│       └── documents.py        # Documents, chunks, FTS5 operations
├── generation/
│   ├── math_reasoning.py       # Deterministic formula derivations and parameters
│   ├── ollama_client.py        # Local Ollama HTTP client
│   ├── output_validation.py    # JSON parsing & citation verification
│   ├── prompts.py              # Prompt templates & passage framing
│   └── provider.py             # LLM provider protocol & factory
├── ingestion/
│   └── normalize.py            # Text normalization & structure-aware chunking
├── retrieval/
│   ├── embeddings.py           # SentenceTransformerProvider (all-MiniLM-L6-v2)
│   └── vector_store.py         # ChromaVectorStore adapter
├── schemas/                    # Pydantic request/response models
└── services/                   # Business logic orchestration
    ├── chat_service.py         # Q&A orchestration, intent routing, idempotency
    ├── conversation_service.py # Conversation thread lifecycle
    ├── document_service.py     # Ingestion, deduplication, deletion, recovery
    ├── index_service.py        # SQLite-to-Chroma index reconstruction
    ├── intent_service.py       # Query intent classification
    ├── search_service.py       # Reciprocal Rank Fusion hybrid search
    └── summary_service.py      # Archive & document summarization
```

---

## 2. Relational Database Schema (`database/connection.py`)

SQLite enforces foreign keys (`PRAGMA foreign_keys = ON`) on every connection.

```sql
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL UNIQUE,
    content_hash TEXT NOT NULL UNIQUE,
    file_type TEXT NOT NULL,
    byte_size INTEGER NOT NULL,
    status TEXT NOT NULL,
    title TEXT,
    source_date TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    error_code TEXT
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    page_number INTEGER,
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(document_id, chunk_index)
);

CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts USING fts5(
    chunk_id UNINDEXED,
    document_id UNINDEXED,
    filename,
    content,
    tokenize = 'porter unicode61'
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    client_turn_id TEXT,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'completed', 'failed')),
    direct_answer TEXT,
    archive_context TEXT,
    limitations TEXT,
    insufficient_evidence INTEGER NOT NULL DEFAULT 0,
    citations TEXT,
    retrieval_count INTEGER NOT NULL DEFAULT 0,
    model TEXT,
    error_message TEXT,
    scope_document_ids TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id, created_at ASC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_idempotency
    ON messages(conversation_id, client_turn_id, role)
    WHERE client_turn_id IS NOT NULL;
```

---

## 3. Application Lifecycle (`app/main.py`)

During application startup (`lifespan` context manager):
1. Verifies that `data_dir`, `files_dir`, and `chroma_path` directories exist.
2. Calls `initialize_database(settings)` to create SQLite tables and FTS5 indexes.
3. Calls `recover_interrupted_documents(settings)` to find any documents left in `processing` or `deleting` states from previous crashes and marks them `failed`.

---

## 4. Error Handling Standard (`core/errors.py`)

All HTTP errors return the uniform `ErrorEnvelope` format:
```json
{
  "error": {
    "code": "MODEL_UNAVAILABLE",
    "message": "The local Ollama service is unreachable.",
    "retryable": true
  }
}
```
Standardized error codes include `VALIDATION_ERROR`, `NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`, `MODEL_UNAVAILABLE`, `MODEL_NOT_FOUND`, `GENERATION_TIMEOUT`, `EMBEDDING_UNAVAILABLE`, and `GENERATION_FAILED`.
