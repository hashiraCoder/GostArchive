# HTTP API Contract

Base URL: `http://127.0.0.1:8000`. JSON uses UTF-8. Request validation errors should return a consistent shape. Use Pydantic schemas; do not leak stack traces or filesystem paths.

## General error envelope

```json
{
  "error": {
    "code": "MODEL_UNAVAILABLE",
    "message": "The local language model is not available.",
    "retryable": true
  }
}
```

## `GET /api/health`

Returns process health only; must not require a model call.

```json
{"status":"ok","app_version":"0.1.0"}
```

## `GET /api/ready`

Checks whether the embedding model, Chroma index, SQLite database, and configured Ollama model are reachable/loaded or available. Report each dependency separately. It may distinguish `ready`, `degraded`, and `unavailable`.

## `POST /api/documents`

Multipart form upload. MVP may accept one file per request; support batch only after single upload is stable. Enforce byte limit and format allowlist (`.txt`, `.md`, and `.pdf` only after PDF phase).

Successful response:

```json
{
  "document": {
    "id": "application-generated-id",
    "filename": "old-letter.md",
    "file_type": "md",
    "status": "ready",
    "chunk_count": 4,
    "created_at": "2026-10-29T00:00:00Z"
  }
}
```

Do not return stored absolute paths or source text in this response.

## `GET /api/documents`

Returns `items` and `total`; stable pagination may be added with `limit`/`offset`. Each item includes ID, display filename, type, size, status, timestamps, and chunk count.

## `GET /api/documents/{document_id}`

Returns metadata only. Do not return full extracted text by default.

## `DELETE /api/documents/{document_id}`

Returns success only after cleanup is complete. If cleanup partially fails, return a stable error and preserve recoverable status.

## `POST /api/search`

Request:

```json
{
  "query": "Where did the writer grow up?",
  "document_ids": [],
  "top_k": 5
}
```

Rules: trim query; enforce a reasonable query-length cap; `top_k` is clamped or rejected outside a safe range; empty `document_ids` means all ready documents.

Response:

```json
{
  "items": [
    {
      "chunk_id": "chunk-id",
      "document_id": "document-id",
      "filename": "journal.md",
      "page_number": null,
      "text": "I grew up in a small village near the river.",
      "score": 0.71
    }
  ],
  "total": 1
}
```

`score` must be documented as the retrieval implementation's similarity/relevance score, not a probability. Do not assume distances from different metrics/models are comparable.

## `POST /api/chat`

Request:

```json
{
  "question": "Where did the writer grow up?",
  "document_ids": [],
  "top_k": 5
}
```

Response:

```json
{
  "answer": "The journal says the writer grew up in a small village near the river.",
  "insufficient_evidence": false,
  "citations": [
    {
      "chunk_id": "chunk-id",
      "document_id": "document-id",
      "filename": "journal.md",
      "page_number": null,
      "excerpt": "I grew up in a small village near the river."
    }
  ],
  "retrieval_count": 1,
  "model": "gemma3:1b"
}
```

Citations must be resolved from database records after generation. The model should return only allowed chunk IDs. Do not accept a model-generated path, page number, filename, or quote as authoritative. If `insufficient_evidence` is true, render it plainly and do not fabricate citations.

## Optional later endpoints

- `GET /api/timeline` — derived event timeline.
- `POST /api/contradictions/analyze` — compare retrieved/selected passages.
- `POST /api/index/rebuild` — internal maintenance route; don't expose destructive admin functionality in UI without explicit need.

Do not build optional endpoints before the import → search → answer path works end to end.
