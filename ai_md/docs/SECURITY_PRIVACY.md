# Security and Privacy Design

## Data boundary

- All source files, extracted text, embeddings, prompts, responses, and indexes remain on the local machine in the MVP.
- First-time setup may download application packages and model/embedding weights. Explain that distinction; after setup, test the actual workflow without network access.
- No hosted LLM, telemetry, analytics, CDN-dependent runtime feature, or remote vector service.
- Keep API bound to loopback. CORS allows only known local frontend origins.

## Threats and mitigations

### Malicious file / path traversal
- Generate stored filename from UUID and allowlisted extension.
- Never use the uploaded filename in filesystem joins.
- Enforce file bytes and extracted text limits.
- Catch parser failures; never accept arbitrary paths or archive extraction in MVP.

### Prompt injection inside an archive
- Treat all imported text as untrusted evidence.
- Delimit source passages and instruct the LLM to ignore embedded instructions.
- Do not give the LLM tools, shell access, filesystem write capability, or arbitrary network access.
- Validate structured output and citation IDs. Prompting is defense-in-depth, not a complete security guarantee.

### Hallucinated citations
- Model can return only chunk IDs supplied in its current context.
- Backend validates IDs and resolves source metadata.
- Do not display model-authored file paths or arbitrary quote text as trusted citation.
- Test unanswerable questions and manually review support.

### Local service exposure
- Bind FastAPI to `127.0.0.1`.
- Do not expose the app through router/port-forwarding or a public tunnel by default.
- Do not assume a local Ollama port is authentication-protected; do not let the app accept arbitrary remote Ollama endpoints in the UI.

### Sensitive data leakage through logs
- Never log raw extracted text, embeddings, chat prompts, or complete model output by default.
- Logs may contain stable IDs, file type, sizes, durations, and non-sensitive error codes.

### Deletion inconsistency
- Delete vectors, chunks, metadata, and source file; handle partial failures without claiming success.
- Provide a local index rebuild/reconciliation path later.

## Privacy claims allowed only after verification

Allowed after testing: “The MVP sends document text to the local Ollama process and uses local storage; no hosted AI API is configured.”

Do not claim: “military-grade”, “perfectly private”, “encrypted”, “zero data leakage”, “hallucination-free”, or “fully offline on first launch” unless independently implemented and evidenced.
