# Search & Retrieval Guide

GhostArchive features a hybrid search engine combining dense semantic embeddings with full-text lexical ranking. This guide explains how to search your archive and understand retrieval scores.

---

## 1. Searching via the Web Interface

1. Navigate to the **Ask Archive** tab or use the search controls.
2. In the search box, enter your query. You can ask conceptual questions (e.g. *"What flowers were discovered in high altitudes?"*) or search for exact identifiers (e.g. *"clc; clear; stem"*).
3. Optionally restrict your search to a specific document by selecting it from the **Scope** dropdown.

---

## 2. Searching via the REST API

### Basic Hybrid Search
```bash
curl -X POST "http://127.0.0.1:8000/api/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "botanical observations in spring",
       "top_k": 5
     }'
```

### Scoped Search (Restricted to Specific Documents)
```bash
curl -X POST "http://127.0.0.1:8000/api/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "temperature variations",
       "top_k": 3,
       "document_ids": ["e9151d30-a48c-4b0f-9b6c-7fd671b7a784"]
     }'
```

---

## 3. Understanding Relevance Badges & Scores

Every retrieved passage displays a relevance label and percentage match:

| Badge Label | Relevance Range | Meaning |
| :--- | :--- | :--- |
| **High match** | Cosine similarity $\ge 50\%$ or rank-0 lexical match with similarity $\ge 35\%$ | Strong conceptual alignment or direct textual quote. |
| **Medium match** | Cosine similarity $\ge 35\%$ or top-3 lexical match with similarity $\ge 25\%$ | Relevant context discussing related concepts. |
| **Relevant** | Cosine similarity $\ge 30\%$ | Supporting background context meeting the calibrated cutoff. |

> **Threshold Filtering:** Any chunk with a similarity score $< 30\%$ is excluded from results to prevent irrelevant text from distracting the model.
