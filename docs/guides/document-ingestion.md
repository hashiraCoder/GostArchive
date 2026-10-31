# Document Ingestion Guide

This guide describes how to import, organize, and manage documents within GhostArchive.

---

## 1. Supported Document Formats

GhostArchive natively supports plain text and Markdown files:
- **Plain Text (`.txt`):** Unformatted UTF-8 text documents, logs, notes, and transcripts.
- **Markdown (`.md`):** Formatted text including headings (`#`, `##`), lists, tables, and fenced code blocks.

> **Note on PDFs and Word Documents:** Binary documents (such as `.pdf` and `.docx`) are not directly ingested in version 0.1.0. Convert them to Markdown or text using Pandoc, `pdftotext`, or a text editor before uploading.

---

## 2. Uploading Documents

### Via the Web Interface
1. Click on the **Documents** tab in the top navigation bar.
2. Drag and drop your `.txt` or `.md` files onto the upload dropzone, or click **Browse Files** to select files from your file explorer.
3. The file upload status will indicate:
   - **Uploading:** Transferring file to local storage.
   - **Processing:** Chunking text and generating local vector embeddings.
   - **Ready:** Document is fully indexed and available for search and Q&A.

### Via the REST API (curl)
```bash
curl -X POST "http://127.0.0.1:8000/api/documents" \
     -H "Accept: application/json" \
     -F "file=@/path/to/my_notes.md"
```
**Example Response:**
```json
{
  "document": {
    "id": "e9151d30-a48c-4b0f-9b6c-7fd671b7a784",
    "original_filename": "my_notes.md",
    "stored_filename": "e9151d30-a48c-4b0f-9b6c-7fd671b7a784.md",
    "file_type": "md",
    "byte_size": 2450,
    "status": "ready",
    "title": "Field Research Notes",
    "source_date": null,
    "chunk_count": 3,
    "created_at": "2026-10-31T12:00:00Z",
    "updated_at": "2026-10-31T12:00:01Z",
    "error_code": null
  },
  "duplicate": false
}
```

---

## 3. Duplicate Document Handling

GhostArchive computes a SHA-256 hash of every uploaded file. If you upload a file with content identical to an existing document in the archive:
- The system skips re-chunking and re-embedding.
- It returns the existing document metadata with `"duplicate": true`.
- No duplicate vectors or chunks are created in storage.

---

## 4. Deleting Documents

### Single Document Deletion
In the **Documents** view:
1. Locate the document in the library table.
2. Click the **Delete** button next to the document.
3. Confirm deletion in the prompt dialog.

### Bulk Document Deletion
1. Select the checkboxes next to multiple documents.
2. Click **Delete Selected** in the table header.
3. All selected documents, their SQLite chunks, FTS5 index records, Chroma vectors, and stored disk files will be permanently deleted.
