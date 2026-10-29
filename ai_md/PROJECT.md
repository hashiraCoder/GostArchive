# GhostArchive — Project Constitution

> This file is the first-read project brief for humans and coding agents. `AGENTS.md` contains engineering invariants; `docs/` contains detailed specifications. If facts conflict, use this precedence: safety/privacy rules in `AGENTS.md` → accepted decisions in `docs/DECISIONS.md` → relevant current specification → implementation. Report conflicts instead of silently guessing.

## What this project is

GhostArchive is a local-first, evidence-grounded AI archive that helps a person rediscover stories from old text files, letters, notes, journals, and documents. A user imports an archive, searches by meaning, asks a question, and receives a concise answer with inspectable citations to the original source passages.

The “Ghost in the Machine” theme is about traces that survive: words, dates, stories, and memories preserved in files. The product must be respectful and grounded. It does not simulate, impersonate, or claim to contact deceased people; it does not fabricate memories.

## Problem and target user

Target user: one privacy-conscious person running the app on their own computer, with a collection of personal, educational, technical, or historical documents.

Problem: the person remembers a subject but not the exact wording or filename. Keyword search is insufficient, and uploading sensitive records to a hosted AI may be unacceptable.

## Core user promise

“Ask questions about your own archive and inspect exactly which original passages support the answer.”

Trust priorities, in order:
1. Source fidelity and valid citations.
2. Honest abstention when evidence is insufficient.
3. Local data handling and clear privacy behavior.
4. Useful retrieval and understandable UI.
5. Visual storytelling and theme polish.

## MVP scope (required)

- Single-user, local desktop-browser experience; no accounts.
- Import `.txt` and `.md` files with size/type validation.
- Extract, normalize, chunk, and index text locally.
- Persist document/chunk metadata in SQLite and embeddings in a local ChromaDB index.
- Semantic search with source locations.
- Ask questions using a local open-weight model served by Ollama.
- Generate answers only from retrieved evidence; validate citation IDs server-side.
- Display source snippets and allow the user to inspect source content.
- Handle no documents, no evidence, invalid files, model unavailable, and indexing errors honestly.
- Delete a document and its related stored/indexed data.
- Provide a repeatable evaluation set, reproducible setup instructions, honest README, and demo.

## Explicitly out of scope for submission MVP

- Reinforcement learning, fine-tuning, training a model, or multi-agent orchestration.
- Hosted AI inference, cloud vector database, analytics/telemetry, cloud sync, user accounts, payment, or SaaS deployment.
- OCR of scanned PDFs, audio transcription, face/image recognition, or impersonating a person.
- Automatic biographies, “truth detection,” guaranteed hallucination-free claims, or deciding which conflicting recollection is true.
- Timeline and contradiction explorer until the RAG MVP is complete and tested.
- Redis, queues, microservices, PostgreSQL, Kubernetes, or complicated deployment infrastructure.

## Chosen stack

- Frontend: React + Vite + TypeScript; Tailwind CSS for styling; a central typed API client; React Router only if separate routes are needed.
- Backend: Python 3.11+ (prefer 3.12 if all dependencies support it), FastAPI, Pydantic v2 / pydantic-settings.
- Local generation: Ollama HTTP API at loopback; default configurable model `gemma3:1b`.
- Embeddings: Sentence Transformers, default `sentence-transformers/all-MiniLM-L6-v2`.
- Vector index: ChromaDB persistent local client.
- Metadata/source of truth: SQLite with parameterized SQL and explicit repositories.
- Tests: pytest + FastAPI TestClient/httpx; Vitest + React Testing Library for frontend when applicable.
- Runtime: Windows 11 first; local-only networking by default.

Exact dependency versions must be captured in lock/requirements files after setup. Do not invent a version in documentation.

## Core flows

1. Import: file → validate → extract → normalize → chunk → embed → persist SQLite metadata/chunks + Chroma vectors → mark ready.
2. Search: question → embed query → retrieve top-k chunks → resolve source metadata from SQLite → render passages.
3. Ask: question → retrieve evidence → if none, abstain → construct prompt with untrusted quoted passages → local Ollama → validate JSON and citation IDs → resolve citations from SQLite → render answer/evidence.
4. Delete: set recoverable state → delete vectors, metadata/chunks, and stored file idempotently → report success only after all required cleanup completes.

## Definition of success

The user can run the app locally, import a small sample archive, search for a paraphrased fact, ask a question, inspect a correct citation, receive an explicit no-evidence response for an unanswerable question, and repeat the workflow after restarting the app. The setup and limitations are documented and tests are actually run.

## Design and delivery posture

Build a verifiable vertical slice in each phase. Never represent a planned capability as implemented. The coding agent must inspect the repository, preserve user changes, run relevant tests, report actual commands/results, and update the phase ledger only with verified facts.
