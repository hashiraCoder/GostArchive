# GhostArchive — Automated Regression Test Case Catalog

**Catalog Version:** 1.0.0  
**Target Release:** 0.1.0  
**Coverage Total:** 230 Automated Tests (194 Backend, 36 Frontend) + 20 Benchmark Scenarios  
**Location:** `docs/testing/TEST_CASES.md`

---

## 1. Backend Test Cases (Pytest Suite — 194 Tests)

### 1.1 Ingestion & Document Lifecycle (`test_documents.py`, `test_ingestion_lifecycle.py`, `test_normalize.py`)
- `test_upload_txt_persists_ready_document`: Ingests clean `.txt` document, verifies SQLite persistence, status `ready`, and chunk offsets.
- `test_upload_invalid_extension_returns_422`: Submits `.pdf` / `.docx` file, verifies HTTP 422 `UNPROCESSABLE_CONTENT`.
- `test_upload_oversized_file_returns_413`: Submits content exceeding 5 MiB, verifies HTTP 413 `CONTENT_TOO_LARGE`.
- `test_duplicate_content_returns_existing_document`: Uploads identical content twice, verifies SHA-256 deduplication and `duplicate: True`.
- `test_empty_text_returns_422`: Submits zero-byte or whitespace-only file, verifies HTTP 422 error.
- `test_document_filtering_and_pagination`: Verifies query, status, file_type filtering, and limit/offset pagination.
- `test_list_and_delete_document`: Deletes document, verifies cascade deletion in SQLite, ChromaDB, and disk.
- `test_bulk_deletion`: Deletes batch of documents with partial ID list, verifies atomic reporting.
- `test_failed_ingestion_sets_failed_status_and_error_code`: Simulates vector failure during ingest, verifies status `failed`.
- `test_startup_recovery_cleans_up_processing_documents`: Simulates server crash during ingest, verifies `recover_interrupted_documents` cleans up stale records on boot.
- `test_normalize_text_removes_invisible_characters`: Tests zero-width spaces (`\u200b`, `\ufeff`) removal.
- `test_normalize_text_normalizes_math_symbols`: Tests unicode operator conversion (`≥` to `>=`, `−` to `-`).
- `test_chunk_text_structure_aware_sampling_theorem`: Verifies headings and code blocks are not severed mid-token.
- `test_chunk_text_source_offsets_valid`: Verifies `start_char` and `end_char` correspond exactly to original normalized text.

### 1.2 Retrieval & Hybrid Ranking (`test_retrieval.py`, `test_remediation.py`, `test_remediation_regression.py`)
- `test_search_resolves_sqlite_metadata_and_bounds_top_k`: Verifies vector query binds to authoritative SQLite rows and respects top_k cap.
- `test_search_drops_orphan_vector`: Injects unreferenced vector into Chroma, verifies retrieval drops orphan.
- `test_rebuild_index_reads_ready_chunks_from_sqlite`: Clears Chroma collection, runs rebuild utility, verifies vectors restored from SQLite.
- `test_real_semantic_search_survives_new_store_instance`: Verifies persistent Chroma storage across client lifecycles.
- `test_search_scope_isolation_restricts_to_selected_document`: Queries with `document_ids` filter, verifies zero leakage from outside docs.
- `test_exact_code_identifier_retrieval_survives_low_similarity`: Verifies lexical boosting for exact code tokens (`clc`, `stem`).
- `test_irrelevant_query_abstains_with_empty_results`: Submits out-of-domain query, verifies empty results under 0.30 similarity threshold.
- `test_fts_porter_stemming_retrieval`: Verifies SQLite FTS5 matches morphological variations (e.g., "pollinates" matches "pollination").
- `test_temporal_intent_detection`: Verifies query containing "latest" or "recent" triggers temporal ordering.
- `test_temporal_ordering_latest_first`: Verifies retrieved passages are ordered with newest date first.
- `test_search_api_no_negative_percentages`: Verifies cosine similarity scores are clamped between 0% and 100%.

### 1.3 Intent Routing & Scoping (`test_intent.py`, `test_phase4_intents_and_scope.py`)
- `test_intent_greeting`: Verifies greetings ("hello", "who are you") classified as `greeting`.
- `test_intent_archive_summary`: Verifies "summarize the archive" classified as `archive_summary`.
- `test_intent_full_document_retrieval`: Verifies "show me the whole file" classified as `full_document_retrieval`.
- `test_intent_conversation_history`: Verifies "what was my last question" classified as `conversation_history`.
- `test_intent_code_explanation`: Verifies "explain the matlab script" classified as `code_explanation`.
- `test_intent_mathematical_calculation`: Verifies "calculate the nyquist rate" classified as `mathematical_calculation`.
- `test_intent_cross_document_synthesis`: Verifies "differences between document A and B" classified as `cross_document_synthesis`.
- `test_full_document_retrieval_with_scope`: Verifies full text dumped when document scoped.
- `test_conversation_history_intent_with_turns`: Verifies conversational recap uses SQLite persistence.

### 1.4 Grounded Generation & Validation (`test_chat.py`, `test_grounded_generation.py`, `test_math_reasoning.py`)
- `test_answer_resolves_only_trusted_citation`: Verifies model output citations match retrieved passages; drops hallucinations.
- `test_empty_retrieval_abstains_without_calling_model`: Verifies immediate return with `insufficient_evidence: True` on empty retrieval.
- `test_prompt_injection_is_framed_as_evidence`: Verifies adversarial instructions inside passages are ignored as instructions.
- `test_invalid_json_is_generation_failure`: Verifies malformed JSON from model raises HTTP 502 `GENERATION_FAILED`.
- `test_ollama_unavailable_is_explicit`: Verifies connection failure to Ollama returns HTTP 503 `MODEL_UNAVAILABLE`.
- `test_math_parameter_extraction_nyquist`: Extracts sampling parameters ($f_m$, $f_s$) and verifies derived calculations.
- `test_code_explanation_matlab_identifiers`: Extracts code identifiers (`clc`, `clear`, `interp1`) for prompt directives.

### 1.5 Conversation Persistence & Idempotency (`test_conversations.py`, `test_conversation_repository.py`)
- `test_auto_creation_and_backward_compatibility`: Verifies conversations auto-created when conversation_id omitted.
- `test_multiturn_context_passed_to_llm`: Verifies up to 3 previous turns passed into prompt.
- `test_scoped_multiturn_context_passed_to_llm`: Verifies turns from different scopes are filtered out.
- `test_bounded_context_window_caps_at_3_turns`: Verifies turns beyond 3 are excluded from prompt.
- `test_failure_handling_and_idempotent_retry`: Verifies retrying failed turn replaces failure.
- `test_idempotency_conflict_on_different_question`: Verifies submitting different question with same `client_turn_id` returns HTTP 409.
- `test_citation_snapshot_survival_after_document_deletion`: Verifies citation text survives source document deletion.
- `test_cascade_delete_removes_messages_cleanly`: Verifies deleting conversation cascade-deletes messages.

### 1.6 Health, Readiness & Reliability (`test_health.py`, `test_model_readiness.py`, `test_api_reliability.py`)
- `test_health_returns_ok`: Verifies `/api/health` returns status `ok`.
- `test_ready_reports_independent_subsystems`: Verifies `/api/ready` inspects database, chroma, embeddings, and Ollama independently.
- `test_ready_503_when_critical_storage_down`: Verifies 503 status code when SQLite inaccessible.
- `test_ollama_not_found_returns_model_not_found`: Verifies missing model in Ollama tags returns `MODEL_NOT_FOUND` with pull instructions.
- `test_422_unprocessable_content_envelope`: Verifies 422 errors return uniform `ErrorEnvelope`.
- `test_404_not_found_envelope`: Verifies 404 errors return uniform `ErrorEnvelope`.
- `test_413_payload_too_large_envelope`: Verifies 413 errors return uniform `ErrorEnvelope`.
- `test_500_unhandled_exception_sanitized_envelope`: Verifies unexpected exceptions return sanitized 500 error envelope.

---

## 2. Frontend Test Cases (Vitest Suite — 36 Tests)

### 2.1 API Client & Error Handling (`client.test.ts`, `ErrorBanner.test.tsx`, `ErrorBoundary.test.tsx`)
- `client.test.ts`:
  1. `apiFetch parses successful JSON responses`
  2. `apiFetch throws ApiException on HTTP 4xx/5xx with parsed ErrorEnvelope`
  3. `apiFetch falls back to generic error when response is not JSON`
  4. `apiFetch handles network drops gracefully`
- `ErrorBanner.test.tsx`:
  1. `renders error code and message`
  2. `renders retry button when retryable=true`
  3. `triggers onRetry callback on button click`
- `ErrorBoundary.test.tsx`:
  1. `renders children when no error occurs`
  2. `catches component render error and renders fallback UI`
  3. `allows resetting error state on retry`

### 2.2 Navigation & Workspace Views (`NavigationViews.test.tsx`, `StatusIndicator.test.tsx`)
- `StatusIndicator.test.tsx`:
  1. `renders loading state`
  2. `renders ready state badge`
  3. `renders degraded state badge`
  4. `renders unavailable state badge`
  5. `polls health endpoint periodically`
- `NavigationViews.test.tsx`:
  1. `renders Overview view by default`
  2. `switches to Documents view on tab click`
  3. `switches to Ask Archive view on tab click`
  4. `switches to History view on tab click`
  5. `switches to System Status view on tab click`
  6. `updates active tab styling`

### 2.3 Document Library & Chat Thread (`DocumentLibrary.test.tsx`, `ConversationThread.test.tsx`, `ConversationSidebar.test.tsx`, `ArchiveWorkspace.test.tsx`)
- `DocumentLibrary.test.tsx`:
  1. `renders empty state when archive has no documents`
  2. `renders document list with titles, chunks, dates`
  3. `triggers delete document confirmation`
- `ConversationThread.test.tsx`:
  1. `renders message bubbles for user and assistant`
  2. `renders evidence citations drawer with percentage badges`
  3. `renders insufficient evidence callout`
- `ConversationSidebar.test.tsx`:
  1. `renders conversation sessions list`
  2. `creates new conversation thread`
  3. `deletes conversation thread`
- `ArchiveWorkspace.test.tsx`:
  1. `coordinates document upload and updates document list`
  2. `filters search results by selected document scope`
  3. `submits question and renders answer in conversation thread`
  4. `handles model offline error with ErrorBanner retry`
  5. `persists active conversation session`
  6. `handles archive summary generation`

---

## 3. Evaluation Benchmark Catalog (`questions.json` — 20 Scenarios)

| ID | Category | Question Summary | Expected Grounding Source | Expected Behavior |
| :--- | :--- | :--- | :--- | :--- |
| `q01` | `answerable_factual` | Botanical specimen discovery date | `botanical_notes.md` | Grounded answer with citation |
| `q02` | `answerable_factual` | Expedition lead researcher name | `botanical_notes.md` | Grounded answer with citation |
| `q03` | `answerable_factual` | Letter destination address in 1887| `letter_to_eliza_1887.txt` | Grounded answer with citation |
| `q04` | `answerable_factual` | Regiment military post in 1944 | `letter_from_the_front_1944.txt`| Grounded answer with citation |
| `q05` | `paraphrased` | Flora specimen temperature limits | `botanical_notes.md` | Paraphrase retrieval hit@5 |
| `q06` | `paraphrased` | Winter weather condition observations | `winter_journal_1923.md` | Paraphrase retrieval hit@5 |
| `q07` | `paraphrased` | Spring thaw timeline and migration | `spring_journal_1923.md` | Paraphrase retrieval hit@5 |
| `q08` | `exact_name` | Full botanical taxonomy identifier | `botanical_notes.md` | Exact name match |
| `q09` | `exact_date` | Date of departure in winter journal | `winter_journal_1923.md` | Exact date match |
| `q10` | `exact_date` | Date of arrival in spring journal | `spring_journal_1923.md` | Exact date match |
| `q11` | `multi_chunk` | Comparison of winter vs spring notes | `winter_journal_1923.md`, `spring_journal_1923.md` | Multi-chunk synthesis |
| `q12` | `multi_chunk` | Expedition supplies budget and route | `botanical_notes.md`, `winter_journal_1923.md` | Multi-chunk synthesis |
| `q13` | `multi_chunk` | Total duration across journal logs | `winter_journal_1923.md`, `spring_journal_1923.md` | Multi-chunk synthesis |
| `q14` | `unanswerable` | Current stock price of technology company | None (Missing from archive) | Abstention (`insufficient_evidence: true`) |
| `q15` | `unanswerable` | Password to expedition storage safe | None (Missing from archive) | Abstention (`insufficient_evidence: true`) |
| `q16` | `unanswerable` | Quantum gravity mathematical equations | None (Missing from archive) | Abstention (`insufficient_evidence: true`) |
| `q17` | `unanswerable` | Secret personal information of author | `unanswerable_subject.txt` | Abstention (`insufficient_evidence: true`) |
| `q18` | `prompt_injection` | Instruction override attempt in query | `adversarial_document.txt` | Treat as evidence, ignore instruction |
| `q19` | `prompt_injection` | System prompt leak attempt | `adversarial_document.txt` | Refuse override, abstain |
| `q20` | `contradiction` | Contradictory accounts of arrival date | `conflicting_accounts.txt` | State both dates in limitations |
