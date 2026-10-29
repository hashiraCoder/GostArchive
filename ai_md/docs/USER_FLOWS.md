# User Flows and UI States

## Primary flow: first run

1. Open GhostArchive.
2. See a short explanation of the local-first promise and which model downloads may be required.
3. See backend, embedding, and generation readiness separately.
4. Import a sample archive or choose local files.
5. Wait for processing state to settle; see failed files with safe reason and retry/delete actions.
6. Search or ask a question.

## Import flow

States: idle → selected → validating → processing → ready / failed.

- Show supported types and size limit before selection.
- Show per-file status, but do not print document contents in logs.
- Disable duplicate submission while the same request is in flight.
- Failed imports are not searchable.
- Never show `ready` while metadata and vectors are inconsistent.

## Search flow

States: empty archive, query input, searching, results, no results, request error.

- Results include readable excerpt, filename, page/offset when available, and a way to open source detail.
- Similarity distance should not be shown as a certainty score.
- Escape or render source text safely; do not interpret markdown/HTML from a document as trusted UI markup.

## Q&A flow

States: no documents, model not ready, waiting, answer, insufficient evidence, generation error.

- Keep cited source cards visible next to or below the answer.
- Clicking a citation opens the exact stored passage, not an inferred path.
- Label AI-generated wording as generated; keep original source text visually distinct.
- If evidence is insufficient, avoid displaying a confident answer with a tiny disclaimer.
- If the source documents disagree, show the disagreement rather than silently choosing one.

## Delete flow

- Ask for confirmation when deleting a document and its index.
- Explain that deletion removes GhostArchive's stored copy/index. Do not claim secure erasure from SSDs, backups, or OS storage.
- Show success only after required storage/index cleanup completes.
- Show a retryable failure state when cleanup is partial.

## Visual principles

- Calm archival tone with subtle mystery, not horror-game aesthetics.
- Strong typographic hierarchy and readable document excerpts.
- Evidence cards are more visually prominent than decorative art.
- Every actionable control has a label, keyboard focus state, and accessible name.
- Respect reduced-motion and narrow viewports.
