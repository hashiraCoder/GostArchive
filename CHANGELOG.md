# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-10-31

### Added
- **Core Local-First Architecture:**
  - FastAPI backend serving REST endpoints bound strictly to loopback `127.0.0.1`.
  - SQLite persistent storage with WAL mode, foreign keys, and FTS5 full-text indexing.
  - ChromaDB persistent vector database with cosine metric space.
  - Sentence Transformers embedding provider using `all-MiniLM-L6-v2`.
  - Local LLM inference integration via Ollama using Google's `gemma3:1b`.
  - Optional `ExternalLLMProvider` protocol for OpenAI-compatible APIs (opt-in only).
- **Document Ingestion & Management:**
  - Support for `.txt` and `.md` document ingestion with 5 MiB file size limits.
  - SHA-256 content deduplication preventing redundant chunking and embedding.
  - Text normalization removing invisible zero-width characters and normalizing math/typographic glyphs.
  - Structure-aware chunking preserving Markdown headings, code blocks, and character offsets.
  - Single and bulk document deletion with cascade cleanup across SQLite, Chroma, and disk.
  - Automatic startup recovery (`recover_interrupted_documents`) for handling sudden power loss.
- **Hybrid Retrieval Engine:**
  - Reciprocal Rank Fusion (RRF) combining dense semantic vector search with SQLite FTS5 Porter stemming.
  - Calibrated relevance threshold filtering (dropping results below 0.30 similarity).
  - Exact code token lexical boosting for identifiers (`clc`, `stem`, `interp1`).
  - Temporal query intent detection and chronological/latest-first sorting.
  - Document-scoped retrieval filtering.
- **Grounded Q&A & Conversation Persistence:**
  - Bounded conversation context window passing up to 3 recent turns for pronoun resolution.
  - Strict evidence framing in system prompt defending against adversarial document injection.
  - Structured JSON generation contract with automated citation validation.
  - Hallucinated citation stripping and limitation consistency checking.
  - Deterministic mathematical derivation engine (`math_reasoning.py`) for exact signal parameter calculations.
  - SQLite conversation persistence with client-side turn idempotency (`client_turn_id`).
  - Frozen citation snapshots surviving source document deletion.
  - Automated abstention (`insufficient_evidence: true`) when evidence is absent.
- **Modern React/TypeScript Frontend:**
  - Responsive single-page application built with React 18, Vite 5, TypeScript 5, and TailwindCSS.
  - 5 workspace navigation views: Overview, Documents, Ask Archive, History, and System Status.
  - React `ErrorBoundary` protecting against unhandled rendering exceptions.
  - System readiness indicator polling subsystem health every 30 seconds.
  - Evidence citation drawer displaying source titles, snippets, and percentage match badges.
  - Standardized `ErrorBanner` component with 1-click retry.
- **Testing & Quality Assurance:**
  - 194 automated Pytest backend tests covering all API endpoints, edge cases, and failure modes.
  - 36 automated Vitest frontend tests covering components, clients, and error boundaries.
  - Deterministic benchmark runner evaluating 20 synthetic questions across 8 categories.
  - 100% clean Ruff linting and formatting across all 68 backend files.
  - Strict TypeScript type checking with zero compiler errors.
