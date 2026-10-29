# Sample Archive — GhostArchive Development and Evaluation Dataset

## Purpose

This directory contains **entirely synthetic, fictional documents** used for:

1. **Development** — providing realistic text-format content during build and integration testing.
2. **Evaluation** — the fixed benchmark referenced in `data/evaluation/questions.json`.

## Important notices

- **No real people.** All names (Margaret Ainsworth, Thomas Ainsworth, Agnes, Dr. Ashworth, Raymond Elsworth, Mr. Drummond, Mr. Fentiman, George Harrington, etc.) are entirely fictional.
- **No real places.** Thornfield House, Greywing Pond, Northbridge, Foleshill Road (used in context), etc. are fictional or used in a fictional context.
- **No real events.** Dates and events are invented for evaluation purposes.
- **No personal information.** Nothing in this directory is based on real personal correspondence, diaries, or records.
- **Safe to commit.** This directory is included in version control because it contains only fictional content needed for reproducible evaluation.

## Document inventory

| File | Format | Evaluation categories covered |
|---|---|---|
| `letters/letter_to_eliza_1887.txt` | `.txt` | Answerable factual, exact date, exact name |
| `letters/letter_from_the_front_1944.txt` | `.txt` | Multi-chunk evidence, exact name, dates |
| `journals/spring_journal_1923.md` | `.md` | Paraphrased retrieval, multi-chunk |
| `journals/winter_journal_1923.md` | `.md` | Exact date, multi-chunk, contradiction setup |
| `notes/botanical_notes.md` | `.md` | Exact name/term search, exact date, paraphrased |
| `notes/unanswerable_subject.txt` | `.txt` | Unanswerable questions (no relevant content) |
| `notes/conflicting_accounts.txt` | `.txt` | Contradictory statements, multi-chunk |
| `injection/adversarial_document.txt` | `.txt` | Prompt injection resistance |

## Evaluation questions

See `../evaluation/questions.json` for the labeled test set (20 questions across 7 categories).

Update the `expected_chunk_ids` in that file after Phase 2 ingestion assigns real chunk IDs.

## Fictional narrative consistency

The documents form a loosely connected archive centered on:
- The **Ainsworth family** across generations (1880s–1940s)
- A **moorland property in Derbyshire** (fictional location)
- Recurring themes: land disputes, botany, wartime correspondence, seasonal journals

This consistency supports multi-chunk retrieval evaluation (questions that require evidence from more than one document).
