"""Tests for Phase C summary endpoint and service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.database.connection import connect, initialize_database
from app.database.repositories.documents import insert_document
from app.services.summary_service import summarize_archive


class FakeOllamaSummary:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = 0

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        assert "personal archive documents" in system_prompt
        return self.response


def test_summarize_empty_archive(temp_settings: Settings, client: TestClient) -> None:
    response = client.post("/api/summarize", json={})
    assert response.status_code == 200
    data = response.json()
    assert "empty" in data["summary"].lower()
    assert data["inspected_documents"] == []


def test_summarize_with_documents(temp_settings: Settings) -> None:
    initialize_database(temp_settings)
    doc = {
        "id": "doc-1",
        "original_filename": "diary_1910.txt",
        "stored_filename": "stored_1.txt",
        "content_hash": "hash1",
        "file_type": "txt",
        "byte_size": 100,
        "status": "ready",
        "title": "Diary 1910",
        "source_date": "1910-01-01",
        "created_at": "2026-10-30T00:00:00",
        "updated_at": "2026-10-30T00:00:00",
        "error_code": None,
    }
    chunks = [
        {
            "id": "doc-1:0",
            "document_id": "doc-1",
            "chunk_index": 0,
            "content": "January 1910: Visited the old windmill on the hill.",
            "page_number": None,
            "start_char": 0,
            "end_char": 48,
            "created_at": "2026-10-30T00:00:00",
        }
    ]
    with connect(temp_settings) as connection:
        insert_document(connection, doc, chunks)

    fake_model = FakeOllamaSummary(
        '{"summary": "Describes visiting an old windmill in 1910.", "limitations": []}'
    )
    result = summarize_archive(temp_settings, ollama_client=fake_model)
    assert fake_model.calls == 1
    assert "windmill" in result["summary"]
    assert len(result["inspected_documents"]) == 1
    assert result["inspected_documents"][0]["filename"] == "diary_1910.txt"
    assert "Archive-wide summary" in result["scope"]


def test_summarize_multi_document_archive(temp_settings: Settings) -> None:
    initialize_database(temp_settings)
    doc1 = {
        "id": "doc-1",
        "original_filename": "diary_1910.txt",
        "stored_filename": "stored_1.txt",
        "content_hash": "hash1",
        "file_type": "txt",
        "byte_size": 100,
        "status": "ready",
        "title": "Diary 1910",
        "source_date": "1910-01-01",
        "created_at": "2026-10-30T00:00:00",
        "updated_at": "2026-10-30T00:00:00",
        "error_code": None,
    }
    chunks1 = [
        {
            "id": "doc-1:0",
            "document_id": "doc-1",
            "chunk_index": 0,
            "content": "January 1910: Visited the old windmill on the hill.",
            "page_number": None,
            "start_char": 0,
            "end_char": 48,
            "created_at": "2026-10-30T00:00:00",
        }
    ]
    doc2 = {
        "id": "doc-2",
        "original_filename": "letters_1920.txt",
        "stored_filename": "stored_2.txt",
        "content_hash": "hash2",
        "file_type": "txt",
        "byte_size": 120,
        "status": "ready",
        "title": "Letters 1920",
        "source_date": "1920-05-01",
        "created_at": "2026-10-30T00:00:00",
        "updated_at": "2026-10-30T00:00:00",
        "error_code": None,
    }
    chunks2 = [
        {
            "id": "doc-2:0",
            "document_id": "doc-2",
            "chunk_index": 0,
            "content": "May 1920: Received a letter from cousin Thomas in London.",
            "page_number": None,
            "start_char": 0,
            "end_char": 56,
            "created_at": "2026-10-30T00:00:00",
        }
    ]
    with connect(temp_settings) as connection:
        insert_document(connection, doc1, chunks1)
        insert_document(connection, doc2, chunks2)

    fake_model = FakeOllamaSummary(
        '{"summary": "Covers diary entries from 1910 and letters from 1920.", "limitations": []}'
    )
    result = summarize_archive(temp_settings, ollama_client=fake_model)
    assert fake_model.calls == 1
    assert len(result["inspected_documents"]) == 2
    filenames = {d["filename"] for d in result["inspected_documents"]}
    assert filenames == {"diary_1910.txt", "letters_1920.txt"}
    assert "covering 2 of 2 ready documents" in result["scope"]


def test_summarize_with_unready_document(temp_settings: Settings) -> None:
    initialize_database(temp_settings)
    doc_ready = {
        "id": "doc-ready",
        "original_filename": "ready.txt",
        "stored_filename": "stored_ready.txt",
        "content_hash": "hash_ready",
        "file_type": "txt",
        "byte_size": 80,
        "status": "ready",
        "title": "Ready File",
        "source_date": None,
        "created_at": "2026-10-30T00:00:00",
        "updated_at": "2026-10-30T00:00:00",
        "error_code": None,
    }
    chunks_ready = [
        {
            "id": "doc-ready:0",
            "document_id": "doc-ready",
            "chunk_index": 0,
            "content": "This is fully indexed content.",
            "page_number": None,
            "start_char": 0,
            "end_char": 30,
            "created_at": "2026-10-30T00:00:00",
        }
    ]
    doc_unready = {
        "id": "doc-processing",
        "original_filename": "processing.txt",
        "stored_filename": "stored_proc.txt",
        "content_hash": "hash_proc",
        "file_type": "txt",
        "byte_size": 90,
        "status": "processing",
        "title": "Processing File",
        "source_date": None,
        "created_at": "2026-10-30T00:00:00",
        "updated_at": "2026-10-30T00:00:00",
        "error_code": None,
    }
    with connect(temp_settings) as connection:
        insert_document(connection, doc_ready, chunks_ready)
        insert_document(connection, doc_unready, [])

    fake_model = FakeOllamaSummary('{"summary": "Summary of ready content.", "limitations": []}')
    result = summarize_archive(temp_settings, ollama_client=fake_model)
    assert len(result["inspected_documents"]) == 1
    assert "covering 1 of 1 ready documents" in result["scope"]
    assert any("not in ready status" in lim for lim in result["limitations"])
