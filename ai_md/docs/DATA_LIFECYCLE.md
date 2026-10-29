# Data Lifecycle and State Model

## Document states

Use these names consistently across SQLite, API responses, and UI:

- `processing`: accepted and currently being extracted/indexed.
- `ready`: source metadata, chunks, and vector records are consistent.
- `failed`: ingestion failed; a safe error code/message may be shown.
- `deleting`: cleanup started but has not yet been fully verified.

Do not invent a `completed` state if the contract uses `ready`. A `failed` document can be retried or deleted. Only `ready` documents are searchable.

## Import lifecycle

1. Receive bytes in a bounded request.
2. Validate allowlisted suffix and optional MIME signal; suffix/MIME are not sufficient alone—parser must succeed.
3. Compute content SHA-256; detect duplicate content before allocating permanent records.
4. Generate a UUID and random storage filename. Store the original under the app-owned data directory, not its supplied name.
5. Extract text; reject empty/unsupported results. Enforce extracted-text limit.
6. Normalize text and deterministically chunk while preserving source offsets/page metadata.
7. Generate embeddings; create SQLite document/chunk records in a controlled transaction and write vectors to Chroma.
8. Set `ready` only after the full index is consistent.
9. If any step fails, clean up created artifacts where safe and record `failed`; never report a successful import if only some stores were written.

Since SQLite and Chroma do not share a transaction, implement compensation and reconciliation explicitly. Do not pretend cross-store atomicity exists.

## Query lifecycle

1. Validate question and optional document IDs.
2. Verify selected documents are `ready`.
3. Embed question and query Chroma using the configured top-k.
4. Resolve vector IDs to authoritative SQLite chunk/source records; drop orphan IDs and record a redacted consistency error.
5. If there are no useful records, return explicit insufficient evidence without model generation where appropriate.
6. Pass only bounded retrieved passages to the model as untrusted quoted data.
7. Validate answer payload and cited IDs against the retrieved ID allowlist.
8. Resolve citation metadata and excerpts from SQLite.
9. Return answer, citations, insufficiency state, and optional non-probabilistic retrieval diagnostics.

## Delete lifecycle

1. Validate the document ID and return not-found if unknown.
2. Persist a `deleting` marker to make an interrupted cleanup discoverable.
3. Delete Chroma records for that document's chunk IDs (or safe metadata filter).
4. Delete SQLite child chunk rows and then document metadata using foreign keys/transaction.
5. Remove the app-managed source file.
6. Mark completion only after all cleanup succeeds. If a store fails, retain enough state for safe retry/reconciliation; do not claim deletion succeeded.
7. Make repeated delete/retry safe and tested.

Exact cleanup ordering can be adjusted based on schema constraints, but it must be idempotent and recovery-aware.

## Privacy boundaries

- Imported bytes, extracted text, embeddings, prompts, and chat questions remain in local storage/processes.
- Logs contain IDs, error codes, timings, and redacted diagnostics, not content.
- Model/embedding download may require internet during setup; runtime should be verified with network disabled.
- Do not say “encrypted” unless encryption at rest is implemented and tested.
