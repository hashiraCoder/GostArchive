# Data Model and Persistence

## 1. Stores

- SQLite: authoritative document metadata, chunk text/source positions, processing status, and optional derived data.
- ChromaDB: vector index containing embedding vectors plus chunk/document identifiers and minimal filter metadata.
- Filesystem: original uploaded files under a private app data directory using generated names. Original user filenames are metadata only; never use them as a raw path component.

Default local data root: `backend/data/` during development. Make it configurable with `GHOSTARCHIVE_DATA_DIR`. Add the runtime directory to `.gitignore`.

## 2. SQLite schema target

### `documents`

- `id TEXT PRIMARY KEY` — application-generated UUID.
- `original_filename TEXT NOT NULL` — display-only, sanitized.
- `stored_filename TEXT NOT NULL UNIQUE` — generated name; no path separators.
- `content_hash TEXT NOT NULL` — SHA-256 of original file bytes.
- `file_type TEXT NOT NULL` — allowed extension/format.
- `byte_size INTEGER NOT NULL`.
- `status TEXT NOT NULL` — `processing | ready | failed | deleting`.
- `title TEXT` — optional extracted title.
- `source_date TEXT` — optional user/doc date; never inferred as certain without evidence.
- `created_at TEXT NOT NULL` — UTC ISO-8601.
- `updated_at TEXT NOT NULL` — UTC ISO-8601.
- `error_code TEXT` — non-sensitive stable code for user-visible failure.

Unique content hash may be used to prevent duplicate imports. If duplicate handling is implemented, return the existing document ID and state the behavior explicitly.

### `document_chunks`

- `id TEXT PRIMARY KEY` — stable application-generated UUID.
- `document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE`.
- `chunk_index INTEGER NOT NULL`.
- `content TEXT NOT NULL`.
- `page_number INTEGER` — 1-based where relevant.
- `start_char INTEGER` and `end_char INTEGER` — optional source offsets.
- `created_at TEXT NOT NULL`.
- `UNIQUE(document_id, chunk_index)`.

### Optional later tables — not MVP blockers

`timeline_events(id, document_id, event_date, date_precision, event_text, source_chunk_ids_json, extraction_status, created_at)`.

`contradictions(id, chunk_a_id, chunk_b_id, summary, review_status, created_at)`.

`conversations` and `messages` are optional. Keep question history in memory/browser state for MVP unless a user need requires persistence.

## 3. Chroma record contract

- ID: exactly `document_chunks.id`.
- Document text: chunk content if Chroma stores it, with SQLite remaining authoritative.
- Metadata: `document_id`, `chunk_index`, `page_number` when present, `file_type`.
- Embedding model name/version should be recorded in configuration and preferably in index metadata. A model change may require rebuilding vectors.

## 4. Transactions and consistency

SQLite and Chroma do not share a transaction. Use an explicit sequence and cleanup compensation:

1. Validate and store the file under a generated temporary name.
2. Extract, chunk, and calculate embeddings.
3. Insert document/chunk metadata in a SQLite transaction.
4. Upsert vectors into Chroma.
5. Mark document `ready` only when both stores are consistent.
6. If a later step fails, clean up created rows/vectors/files where safe and mark failure visibly.

For delete:
1. Mark document `deleting`.
2. Delete vector records filtered by document ID / chunk IDs.
3. Delete SQLite document row (cascade removes chunks).
4. Delete original file.
5. If any step fails, keep a recoverable state and show failure; never report full success prematurely.

The exact delete order can be adjusted for safe retries, but it must be idempotent and tested for partial failure.

## 5. SQLite settings

- Enable foreign keys for each connection (`PRAGMA foreign_keys=ON`).
- Use parameterized SQL.
- Use WAL only if needed; keep configuration deliberate.
- Run schema migrations as numbered SQL files if the schema evolves. For the MVP, one initialization schema is enough, but don't silently mutate schema in many unrelated places.
