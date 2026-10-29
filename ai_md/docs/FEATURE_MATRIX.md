# Feature Matrix and Priority

Status vocabulary: `MVP REQUIRED`, `MVP OPTIONAL`, `POST-SUBMISSION`, `OUT OF SCOPE`.

| Feature | Priority | Description | Acceptance evidence |
|---|---|---|---|
| Local app shell | MVP REQUIRED | Frontend talks to loopback FastAPI | Visible API health and failure state |
| `.txt` import | MVP REQUIRED | Validate, extract, index | Tests with valid/empty/oversized files |
| `.md` import | MVP REQUIRED | Preserve headings and paragraph structure as text | Tests with Unicode and code fences |
| PDF extraction | MVP OPTIONAL | Text-based PDFs only; no OCR | Page-aware source tests; do not ship if unstable |
| File duplicate detection | MVP REQUIRED | SHA-256 by content | Repeat import gives documented result |
| Chunking | MVP REQUIRED | Stable IDs and source offsets | Boundary/empty/long-text tests |
| Local embeddings | MVP REQUIRED | Sentence Transformers | Retrieval test set works after restart |
| Persistent vector search | MVP REQUIRED | ChromaDB local persistent client | Index persists and can be rebuilt |
| Grounded Q&A | MVP REQUIRED | Local model, retrieved source context | Answerable/unanswerable examples pass stated gates |
| Citation viewer | MVP REQUIRED | View source passage and metadata | Citation ID/source resolution tests |
| Explicit abstention | MVP REQUIRED | No answer when no evidence | Fixed unsupported-question test |
| Model readiness | MVP REQUIRED | Report if Ollama/model is missing | Offline/missing-model UI state |
| Delete lifecycle | MVP REQUIRED | Remove files, metadata, vectors | Integration test and retry behavior |
| Theme/visual polish | MVP REQUIRED | Distinctive archival style but readable | Responsive/manual demo check |
| Evaluation runner | MVP REQUIRED | Reproducible tests/metrics | Command and raw output documented |
| Timeline extraction | POST-SUBMISSION | Date-aware event view | Event citations plus date-type semantics |
| Contradiction explorer | POST-SUBMISSION | Show competing claims and sources | Tests for true and false conflicts |
| OCR/audio/photos | POST-SUBMISSION | Only with consent and privacy review | Separate evaluated pipelines |
| Cloud sync/login/analytics | OUT OF SCOPE | Not required for local MVP | Do not implement |
| RL/fine-tuning/multi-agent | OUT OF SCOPE | Not needed for core product | Do not implement |
