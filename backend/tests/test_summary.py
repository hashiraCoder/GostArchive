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
