# Product Specification

## 1. Product promise

GhostArchive helps a person rediscover what their own archive says. It does not simulate a deceased person, claim to contact spirits, or invent personal history. The “ghost” is the trace left by words that survived their author or moment.

## 2. Target user and problem

A person has a collection of notes, letters, diaries, technical notes, or historical documents. They remember a topic or event but do not remember the exact filename or wording. Keyword search is insufficient. Hosted AI can require uploading sensitive documents to someone else's servers. GhostArchive enables local, source-grounded search and answers.

## 3. Core user stories

- As a user, I can import a supported text document and see its processing state.
- As a user, I can search a question by meaning and see matching passages.
- As a user, I can ask a question and see a concise answer with citations to original documents.
- As a user, I can open a citation and inspect the exact source passage and page/character location.
- As a user, I can see when there is no useful evidence instead of receiving a made-up answer.
- As a user, I can delete a document and its indexed representation.
- As a user, I can tell whether the backend and local model are ready.

## 4. MVP acceptance requirements

1. App runs locally on Windows with explicit prerequisites.
2. Import `.txt` and `.md`; optional PDF extraction must be text-based and tested (scanned PDFs/OCR are out of scope).
3. File type/size/text limits are enforced.
4. Duplicate imports are detected by content hash or clearly documented as allowed.
5. Chunks retain document ID, chunk index, and source position/page where available.
6. Semantic search returns ranked passages with stable IDs and source metadata.
7. Chat uses the local Ollama endpoint only, and only retrieved passages are supplied as archive-specific evidence.
8. The API validates citation IDs and resolves labels/paths/page information from trusted records.
9. No-evidence and model-unavailable states are explicit; no fake success or canned answer.
10. Deletion removes the source file, metadata, chunks, and vectors; partial failures are visible and retryable.
11. A deterministic evaluation set includes answerable and unanswerable queries.
12. README includes setup, model setup, privacy behavior, license/attribution, limitations, and demo instructions.

## 5. Non-goals for MVP

- Reconstructing a person's personality or impersonating the dead.
- OCR for scanned images, face recognition, image similarity, or audio transcription.
- Timeline, named-entity graph, automatic biography, or contradiction explorer unless core MVP is stable.
- Multi-user/cloud SaaS, sync, analytics, hosted inference, user authentication, or payment.
- Model training, fine-tuning, reinforcement learning, or multi-agent orchestration.

## 6. UX principles

- Evidence before atmosphere: the source passage must be easier to find than decorative elements.
- Respectful, non-sensational language for family history.
- The interface labels generated summaries as AI-generated and preserves exact source text separately.
- Empty, loading, error, low-evidence, and model-offline states are first-class designs.
- Avoid claims such as “perfect recall”, “truth detector”, or “hallucination-free”.

## 7. Success metrics to measure

Use a fixed manually labeled test dataset. Report actual values only after running it:
- Recall@5 / Hit@5 for source retrieval.
- Citation ID validity rate.
- Citation support rate from manual review.
- Unanswerable-query abstention rate.
- False abstention rate for answerable queries.
- Indexing time and answer latency on the actual test laptop.
