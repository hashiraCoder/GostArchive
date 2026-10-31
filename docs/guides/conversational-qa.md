# Conversational Q&A & Evidence Grounding Guide

This guide explains how to ask questions across your archive, how multi-turn conversations work, and how citations are validated.

---

## 1. Asking Questions

Navigate to the **Ask Archive** tab in the GhostArchive interface:
1. **Choose Scope:** Select **Entire Archive** to search across all uploaded documents, or select a specific document from the dropdown to focus your inquiry.
2. **Type Question:** Enter your question in the text box (e.g., *"What was the agreed budget for the northern expedition?"*).
3. **Submit:** Press `Enter` or click **Ask**.

---

## 2. Reading Grounded Answers

A typical answer contains four primary sections:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ DIRECT ANSWER                                                          │
│ The agreed budget for the northern expedition was £1,200, finalized   │
│ in the March meeting.                                                  │
├────────────────────────────────────────────────────────────────────────┤
│ ARCHIVE CONTEXT                                                        │
│ Initial estimates in January suggested £800, but logistics costs were │
│ revised upwards following equipment procurement reviews.              │
├────────────────────────────────────────────────────────────────────────┤
│ LIMITATIONS & AMBIGUITIES                                              │
│ - Final accounting receipts for equipment are not recorded in archive. │
├────────────────────────────────────────────────────────────────────────┤
│ EVIDENCE CITATIONS (2 Passages)                                        │
│ [Passage 1] winter_journal_1923.md (Match: 82%)                        │
│ "...the finalized budget agreed upon by all parties is twelve hundred..."│
└────────────────────────────────────────────────────────────────────────┘
```

1. **Direct Answer:** The concise, factual conclusion grounded strictly in the text.
2. **Archive Context:** Additional nuances or background details mentioned in the documents.
3. **Limitations:** Explicit notes on ambiguities, conflicting accounts, or missing information.
4. **Evidence Citations:** The exact quoted passages from your files that support the answer.

---

## 3. Multi-Turn Conversations & Pronoun Resolution

GhostArchive remembers conversational context across turns within the same thread:

```text
User: Who authored the botanical field journal?
Assistant: Arthur Pendelton authored the botanical journal during his 1923 expedition.
           [Citation: botanical_notes.md]

User: What was his primary finding in that journal?
Assistant: Arthur Pendelton observed that the Alpine Saxifrage flowered three weeks
           earlier than expected due to unseasonal warmth.
           [Citation: botanical_notes.md]
```

- **Pronoun Resolution:** The model understands that "his" refers to Arthur Pendelton from the previous turn.
- **Context Cap:** To preserve context window capacity and prevent stale drift, GhostArchive includes up to the **3 most recent completed turns** in the prompt.
- **Scope Isolation:** If you switch document scope between turns, earlier turns from outside the active scope are excluded to prevent cross-document confusion.

---

## 4. Understanding Abstention ("Insufficient Evidence")

If you ask a question that cannot be answered from your documents:
```text
User: What is the current price of gold?
Assistant: Insufficient Evidence
"The archive contains no documents or records mentioning current gold prices or modern commodities."
[Citations: None]
```
GhostArchive will never invent a plausible answer from general pre-training knowledge. It will tell you clearly what information is missing.
