# GhostArchive REST API Reference

The GhostArchive backend provides a RESTful API mounted under `/api`. All endpoints accept and return JSON.

**Default Base URL:** `http://127.0.0.1:8000/api`

---

## 1. Uniform Error Response Schema

All HTTP errors return an `ErrorEnvelope`:
```json
{
  "error": {
    "code": "MODEL_UNAVAILABLE",
    "message": "The local Ollama service is unreachable.",
    "retryable": true
  }
}
```

### Standard Error Codes
| Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `VALIDATION_ERROR` | 422 | Request body or query parameters failed schema validation. |
| `NOT_FOUND` | 404 | Requested document or conversation resource was not found. |
| `CONFLICT` | 409 | Conflicting concurrent turn in progress, or idempotency conflict. |
| `CONTENT_TOO_LARGE` | 413 | Uploaded file or extracted text exceeds configured size limits. |
| `MODEL_UNAVAILABLE` | 503 | Local Ollama daemon is offline or unreachable. |
| `MODEL_NOT_FOUND` | 503 | Configured model tag is not downloaded in Ollama. |
| `GENERATION_TIMEOUT` | 504 | Model inference exceeded configured timeout limit. |
| `EMBEDDING_UNAVAILABLE` | 503 | Sentence Transformers embedding model unavailable. |
| `GENERATION_FAILED` | 502 | Model returned malformed or unparseable output. |
| `INTERNAL_ERROR` | 500 | Unhandled server error (details sanitized from client). |

---

## 2. Health & Readiness Endpoints

### 2.1 Liveness Probe
- **Endpoint:** `GET /api/health`
- **Description:** Fast process health check. Does not perform I/O or model calls.
- **Response (200 OK):**
```json
{
  "status": "ok",
  "app_version": "0.1.0"
}
```

### 2.2 Deep Readiness Probe
- **Endpoint:** `GET /api/ready`
- **Query Parameters:** `check_inference=true` (optional active generation probe)
- **Description:** Checks SQLite storage, ChromaDB, Sentence Transformers, and Ollama status.
- **Response (200 OK / 503 Service Unavailable):**
```json
{
  "overall": "ready",
  "dependencies": {
    "document_storage": { "status": "ready", "message": "SQLite and ChromaDB storage accessible" },
    "embedding_service": { "status": "ready", "message": "Model ready (sentence-transformers/all-MiniLM-L6-v2)" },
    "ollama_service": { "status": "ready", "message": "Ollama daemon reachable at http://127.0.0.1:11434" },
    "model_available": { "status": "ready", "message": "Model 'gemma3:1b' installed in local Ollama" },
    "model_inference": { "status": "ready", "message": "Model available for inference" }
  }
}
```

---

## 3. Documents Endpoints

### 3.1 Upload Document
- **Endpoint:** `POST /api/documents`
- **Content-Type:** `multipart/form-data`
- **Form Field:** `file` (UploadFile)
- **Response (201 Created):**
```json
{
  "document": {
    "id": "e9151d30-a48c-4b0f-9b6c-7fd671b7a784",
    "original_filename": "botanical_notes.md",
    "stored_filename": "e9151d30-a48c-4b0f-9b6c-7fd671b7a784.md",
    "file_type": "md",
    "byte_size": 2760,
    "status": "ready",
    "title": "botanical_notes",
    "source_date": null,
    "chunk_count": 3,
    "created_at": "2026-10-31T12:00:00Z",
    "updated_at": "2026-10-31T12:00:01Z",
    "error_code": null
  },
  "duplicate": false
}
```

### 3.2 List Documents
- **Endpoint:** `GET /api/documents`
- **Query Parameters:**
  - `query` (string, max 200 chars)
  - `status` (string: `ready`, `processing`, `failed`, `deleting`)
  - `file_type` (string: `txt`, `md`)
  - `limit` (int, 1–100, default 50)
  - `offset` (int, default 0)
- **Response (200 OK):**
```json
{
  "items": [ ... ],
  "total": 12
}
```

### 3.3 Delete Document
- **Endpoint:** `DELETE /api/documents/{document_id}`
- **Response:** `204 No Content`

### 3.4 Bulk Delete Documents
- **Endpoint:** `POST /api/documents/bulk-delete`
- **Request Body:**
```json
{
  "document_ids": ["id-1", "id-2"]
}
```
- **Response (200 OK):**
```json
{
  "results": { "id-1": true, "id-2": true },
  "total_deleted": 2
}
```

---

## 4. Search Endpoint

### 4.1 Hybrid Search
- **Endpoint:** `POST /api/search`
- **Request Body:**
```json
{
  "query": "botanical survey timeline",
  "top_k": 5,
  "document_ids": null
}
```
- **Response (200 OK):**
```json
{
  "items": [
    {
      "chunk_id": "c6fa4d52-...",
      "document_id": "e9151d30-...",
      "filename": "botanical_notes.md",
      "text": "Passage text...",
      "similarity_score": 0.824,
      "relevance_label": "High match",
      "source_date": "1923-04-12"
    }
  ],
  "total": 1
}
```

---

## 5. Chat & Q&A Endpoint

### 5.1 Ask Grounded Question
- **Endpoint:** `POST /api/chat`
- **Request Body:**
```json
{
  "question": "When did the expedition arrive at northern camp?",
  "conversation_id": "opt-conv-uuid",
  "client_turn_id": "opt-turn-uuid",
  "top_k": 5,
  "document_ids": null
}
```
- **Response (200 OK):**
```json
{
  "conversation_id": "b3e1075b-...",
  "answer": "The expedition arrived at the northern camp on March 14, 1923.",
  "archive_context": "Initial travel was delayed by heavy blizzard conditions in February.",
  "limitations": [],
  "insufficient_evidence": false,
  "citations": [
    {
      "chunk_id": "c6fa4d52-...",
      "document_id": "e9151d30-...",
      "title": "Winter Journal",
      "filename": "winter_journal_1923.md",
      "passage_text": "...arrived at the northern camp on March 14...",
      "relevance_score": 0.88,
      "document_present": true
    }
  ],
  "retrieval_count": 1,
  "model": "gemma3:1b"
}
```

---

## 6. Conversations Endpoints

### 6.1 List Conversations
- **Endpoint:** `GET /api/conversations?limit=50&offset=0&query=search`
- **Response (200 OK):**
```json
{
  "items": [
    {
      "id": "b3e1075b-...",
      "title": "Expedition Arrival Inquiry",
      "created_at": "2026-10-31T12:00:00Z",
      "updated_at": "2026-10-31T12:05:00Z",
      "message_count": 4,
      "last_message_preview": "The expedition arrived at the northern camp..."
    }
  ],
  "total": 1
}
```

### 6.2 Get Conversation Detail
- **Endpoint:** `GET /api/conversations/{conversation_id}`
- **Response (200 OK):** Returns full thread including user and assistant message records with frozen citation snapshots.

### 6.3 Rename Conversation
- **Endpoint:** `PATCH /api/conversations/{conversation_id}`
- **Request Body:** `{ "title": "Updated Title" }`
- **Response (200 OK):** Updated conversation summary.

### 6.4 Delete Conversation
- **Endpoint:** `DELETE /api/conversations/{conversation_id}`
- **Response:** `204 No Content` (cascades to all associated messages in SQLite).

---

## 7. Summarize Endpoint

### 7.1 Summarize Archive or Document
- **Endpoint:** `POST /api/summarize`
- **Request Body:**
```json
{
  "document_id": null,
  "max_chunks": 10
}
```
- **Response (200 OK):**
```json
{
  "summary": "The archive contains historical expedition journals and botanical notes from 1923...",
  "document_count": 3,
  "chunk_count": 9,
  "model": "gemma3:1b"
}
```
