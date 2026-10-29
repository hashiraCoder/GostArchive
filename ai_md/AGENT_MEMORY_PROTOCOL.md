# Coding-Agent Memory Protocol

## Why these files exist

Agent context is split by purpose so agents can reload the right facts without stuffing every specification into every prompt.

- `PROJECT.md`: stable product identity, promise, scope, and chosen stack. Read first.
- `AGENTS.md`: always-on engineering and safety invariants. Canonical rules for all agents.
- Tool entrypoints (`GEMINI.md`, `CLAUDE.md`, Copilot instructions, Cursor and Antigravity rules): brief adapter context; they point to canonical files and must not create conflicting policy.
- `docs/PROJECT_MEMORY.md`: project-specific durable facts and latest verified implementation state.
- `docs/DECISIONS.md`: append architecture decisions and their rationale. Do not rewrite history to disguise a change.
- `docs/PHASE_CHECKLIST.md`: checked acceptance gates only. Never check an item based solely on code generation.
- `docs/KNOWN_ISSUES.md`: active defects, blockers, and follow-up items (create when the first real issue is discovered). If the file does not exist, do not claim it exists; create it when there is a verified issue to track.
- `docs/`: detailed specs; the relevant specification governs the current change.

## Required boot sequence

At the start of work:
1. Read `PROJECT.md`.
2. Read `AGENTS.md` and the current `docs/PROJECT_MEMORY.md`.
3. Read the relevant feature specification(s) and phase checklist.
4. Inspect the actual files and git status; do not trust stale memory over repository truth.
5. State the targeted files, intended behavior, and verification steps.

## During work

- Keep work to one phase or clearly scoped issue.
- If the implementation conflicts with documented decisions, stop and explain the conflict before making a breaking architectural change.
- Ask only when an essential product decision cannot be inferred; otherwise follow this pack and call out assumptions.
- Do not create fake data in production paths, fake successful status messages, pretend external tools ran, or claim local inference was tested unless it was.
- Avoid broad refactors while implementing a narrow feature.

## At the end of a task

1. Run the tests appropriate to the changed code and any integration check possible locally.
2. Inspect `git diff` and ensure no secrets or runtime data are staged.
3. Report files changed, behavior, actual commands run, pass/fail output, untested conditions, and remaining work.
4. Update `docs/PHASE_CHECKLIST.md` only for acceptance criteria proven by evidence.
5. Update `docs/PROJECT_MEMORY.md` with verified repository facts if they changed.
6. Append significant architectural decisions to `docs/DECISIONS.md`.

## Memory hygiene

- Store stable, useful facts only; do not dump conversation transcripts into memory.
- Do not duplicate the entire spec into `PROJECT_MEMORY.md`.
- Separate `planned`, `implemented`, `tested`, and `released` states.
- Never store secrets, personal documents, access tokens, precise personal details, or private archive content in project memory.
- When changing a default (stack, endpoint, database schema, model), update canonical docs and all references in one task.
