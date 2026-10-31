"""Tests for ConversationRepository and foreign-key cascades."""

from app.core.config import Settings
from app.database.connection import connect, initialize_database
from app.database.repositories import conversations as repo
from app.database.repositories.documents import insert_document


def test_conversation_crud_and_foreign_key_cascade(temp_settings: Settings) -> None:
    initialize_database(temp_settings)
    with connect(temp_settings) as conn:
        # 1. Create conversation
        conv = repo.create_conversation(conn, "Test Conversation")
        cid = conv["id"]
        assert conv["title"] == "Test Conversation"

        # 2. Get conversation
        fetched = repo.get_conversation(conn, cid)
        assert fetched is not None
        assert fetched["title"] == "Test Conversation"

        # 3. Add messages
        msg_user = repo.add_message(
            conn,
            cid,
            role="user",
            content="Hello archive",
            client_turn_id="turn-1",
        )
        assert msg_user["role"] == "user"
        assert msg_user["status"] == "completed"

        msg_asst = repo.add_message(
            conn,
            cid,
            role="assistant",
            content="",
            status="pending",
            client_turn_id="turn-1",
        )
        assert msg_asst["status"] == "pending"

        # Update assistant message
        updated = repo.update_assistant_message(
            conn,
            msg_asst["id"],
            status="completed",
            content="Hello user",
            direct_answer="Hello user",
            citations=[
                {"chunk_id": "c1", "document_id": "d1", "filename": "f.txt", "excerpt": "text"}
            ],
        )
        assert updated is not None
        assert updated["status"] == "completed"
        assert updated["content"] == "Hello user"
        assert len(updated["citations"]) == 1

        # 4. List messages
        messages = repo.list_messages(conn, cid)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["citations"][0]["document_exists"] is False  # d1 not in documents table

        # 5. List conversations
        conv_list = repo.list_conversations(conn)
        assert len(conv_list) >= 1
        assert conv_list[0]["id"] == cid
        assert conv_list[0]["message_count"] == 2
        assert conv_list[0]["last_message_preview"] == "Hello user"

        # 6. Rename conversation
        renamed = repo.update_conversation_title(conn, cid, "Renamed Title")
        assert renamed is not None
        assert renamed["title"] == "Renamed Title"

        # 7. Foreign-key cascade: Deleting conversation MUST delete messages
        deleted = repo.delete_conversation(conn, cid)
        assert deleted is True

        # Assert conversation gone
        assert repo.get_conversation(conn, cid) is None
        # Assert messages cascaded
        msg_rows = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (cid,)
        ).fetchone()
        assert msg_rows[0] == 0


def test_citation_preservation_with_document_presence(temp_settings: Settings) -> None:
    initialize_database(temp_settings)
    with connect(temp_settings) as conn:
        # Insert a real document
        doc_id = "test-doc-123"
        doc_data = {
            "id": doc_id,
            "original_filename": "notes.txt",
            "stored_filename": "uuid.txt",
            "content_hash": "hash123",
            "file_type": "txt",
            "byte_size": 100,
            "status": "ready",
            "title": "Notes",
            "source_date": None,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "error_code": None,
        }
        insert_document(conn, doc_data, [])

        # Create conversation and assistant message citing this doc
        conv = repo.create_conversation(conn, "Citation Thread")
        cid = conv["id"]
        repo.add_message(
            conn,
            cid,
            role="assistant",
            content="Answer citing document",
            status="completed",
            citations=[
                {
                    "chunk_id": f"{doc_id}:1",
                    "document_id": doc_id,
                    "filename": "notes.txt",
                    "excerpt": "quoted text",
                    "page_number": None,
                    "evidence_type": "direct",
                }
            ],
        )

        # Before document deletion: document_exists must be True
        msgs_before = repo.list_messages(conn, cid)
        assert msgs_before[0]["citations"][0]["document_exists"] is True

        # Delete the document from documents table
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

        # After document deletion: historical citation STILL RENDERS, but document_exists is False
        msgs_after = repo.list_messages(conn, cid)
        assert len(msgs_after) == 1
        assert msgs_after[0]["citations"][0]["excerpt"] == "quoted text"
        assert msgs_after[0]["citations"][0]["filename"] == "notes.txt"
        assert msgs_after[0]["citations"][0]["document_exists"] is False


def test_stale_turn_recovery(temp_settings: Settings) -> None:
    initialize_database(temp_settings)
    with connect(temp_settings) as conn:
        conv = repo.create_conversation(conn, "Crash Recovery")
        cid = conv["id"]

        # Add a pending message simulating a crashed worker from 100 seconds ago
        msg = repo.add_message(conn, cid, role="assistant", content="", status="pending")
        conn.execute(
            "UPDATE messages SET created_at = '2026-01-01T00:00:00Z' WHERE id = ?",
            (msg["id"],),
        )

        # Checking pending turns with 60s timeout recovers the stale turn to failed
        pending = repo.check_pending_turn(conn, cid, timeout_seconds=60)
        assert pending is None  # Reclaimed

        # Message is now marked failed with timeout notice
        reclaimed = conn.execute(
            "SELECT status, error_message FROM messages WHERE id = ?", (msg["id"],)
        ).fetchone()
        assert reclaimed["status"] == "failed"
        assert "timed out" in reclaimed["error_message"].lower()


def test_recent_turns_scope_isolation(temp_settings: Settings) -> None:
    initialize_database(temp_settings)
    with connect(temp_settings) as conn:
        conv = repo.create_conversation(conn, "Scope Thread")
        cid = conv["id"]

        # Turn 1: scoped to doc A
        repo.add_message(
            conn, cid, role="user", content="Q1", status="completed", scope_document_ids=["doc_a"]
        )
        repo.add_message(
            conn,
            cid,
            role="assistant",
            content="A1 about doc A",
            status="completed",
            scope_document_ids=["doc_a"],
        )

        # Turn 2: scoped to all docs
        repo.add_message(
            conn, cid, role="user", content="Q2", status="completed", scope_document_ids=[]
        )
        repo.add_message(
            conn,
            cid,
            role="assistant",
            content="A2 about all docs",
            status="completed",
            scope_document_ids=[],
        )

        # Active turn is scoped strictly to doc A:
        # Assistant response A2 (from broader scope) must be excluded from generation context!
        turns = repo.get_recent_completed_turns(
            conn, cid, limit_turns=3, active_scope_ids=["doc_a"]
        )
        # Should include Q1, A1, and Q2 (for reference resolution), but NOT A2!
        contents = [t["content"] for t in turns]
        assert "A1 about doc A" in contents
        assert "A2 about all docs" not in contents
