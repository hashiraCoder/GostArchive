# Product Scope and Requirements

## Product statement

GhostArchive is a private, local-first archive explorer. It retrieves and explains information contained in a user's own documents, preserving provenance so the user can verify the answer.

## Persona

A single individual has a folder of old letters, notes, journals, study material, or project notes. The user knows approximately what they are looking for but cannot locate it quickly. They value privacy and want answers that can be checked against original text.

## User jobs

- Find a passage using meaning rather than exact keywords.
- Ask a question spanning multiple documents.
- Open the evidence that supports an answer.
- Know when the archive does not contain an answer.
- Import, list, and delete documents without losing control of local files.
- See whether indexing and local model dependencies are ready.

## Functional requirements

### FR-01 Import
Accept `.txt` and `.md` for the MVP. Enforce configurable maximum bytes and extracted characters. Use server-generated document IDs and storage names. Detect duplicate content with SHA-256; communicate whether it was skipped or already exists. No user filename may control the storage path.

### FR-02 Extraction and chunking
Normalize line endings while preserving paragraph breaks and punctuation. Create deterministic chunk IDs with document ID, chunk index, and source offsets. Avoid empty chunks and ensure the chunker always advances. PDF support is optional and must preserve page numbers if enabled.

### FR-03 Local indexing
Create embeddings locally. Persist vector records in ChromaDB and authoritative document/chunk text and metadata in SQLite. Record the embedding model identifier in settings or index metadata. Make index rebuild possible from SQLite.

### FR-04 Search
Search semantically with a bounded configurable top-k (default 5, max 8 initially). Optionally filter by document IDs. Return stable chunk IDs and backend-resolved source metadata. Do not present distance as calibrated confidence.

### FR-05 Grounded Q&A
Use the local Ollama endpoint only. Provide a bounded set of retrieved chunks, clearly labeled as untrusted evidence. Require structured output with answer, insufficient-evidence indicator, and cited chunk IDs. Verify schema and IDs server-side. Resolve display filenames, page numbers, quotes, and source links from trusted records—not model output.

### FR-06 Evidence UI
Render the answer and linked source cards. Users must be able to inspect the exact stored passage. If model output is invalid, show an actionable error rather than fabricating a response.

### FR-07 Readiness and failure states
Expose app health separately from dependency readiness. Show Ollama/model, embedding model, SQLite, and vector-store state where feasible. Search remains usable without generation if its dependencies are ready. A missing model must not be presented as ready.

### FR-08 Delete
Delete the original stored file, SQLite document/chunk records, and Chroma records. Handle partial failure safely; state should be retryable and success must not be returned before all cleanup is complete.

### FR-09 Evaluation
Ship a small fixed benchmark with answerable, paraphrased, multi-chunk, unanswerable, unrelated, and prompt-injection-containing examples. Include known expected supporting chunk IDs and a documented evaluation command.

## Non-functional requirements

- Local-first: no document content, questions, embeddings, or prompts leave the local machine during normal runtime.
- Safety: prompt injection within a document is treated as data, never privileged instruction.
- Traceability: every displayed citation is backed by a persisted chunk record.
- Reliability: invalid inputs, corrupt documents, model timeouts, and store inconsistency have explicit errors.
- Accessibility: keyboard navigation, visible focus, semantic labels, sufficient contrast, responsive layout.
- Maintainability: typed API schemas, focused services, centralized configuration and API client, tests for user-visible behavior.
- Reproducibility: setup instructions work from a fresh checkout on Windows.

## Acceptance gates

The MVP is not complete until all required paths are tested: import → indexing → search → grounded answer → inspect source → restart persistence → delete. At least one unanswerable query and one injected-document test must be included. Report measured results; do not invent metrics.

## Future scope (not submission blockers)

1. PDF text extraction (non-scanned only).
2. Timeline with explicit source for every event date and distinction between document date and event date.
3. Contradiction explorer that presents competing passages without deciding which is true.
4. Optional local speech-to-text for oral history.
5. Better hybrid lexical/semantic retrieval and reranking, if measurements justify it.
6. Packaging as a desktop app; only after local web app is stable.
