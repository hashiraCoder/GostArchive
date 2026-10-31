"""SQLite connection and schema initialization."""

from __future__ import annotations

import sqlite3

from app.core.config import Settings


def connect(settings: Settings) -> sqlite3.Connection:
    """Open a configured SQLite connection with foreign keys enabled."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(settings: Settings) -> None:
    """Create the MVP schema when it does not exist."""
    with connect(settings) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL UNIQUE,
                content_hash TEXT NOT NULL UNIQUE,
                file_type TEXT NOT NULL,
                byte_size INTEGER NOT NULL,
                status TEXT NOT NULL,
                title TEXT,
                source_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                error_code TEXT
            );

            CREATE TABLE IF NOT EXISTS document_chunks (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                page_number INTEGER,
                start_char INTEGER NOT NULL,
                end_char INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(document_id, chunk_index)
            );

            CREATE INDEX IF NOT EXISTS idx_documents_status
                ON documents(status);
            CREATE INDEX IF NOT EXISTS idx_chunks_document_id
                ON document_chunks(document_id);

            CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts USING fts5(
                chunk_id UNINDEXED,
                document_id UNINDEXED,
                filename,
                content,
                tokenize = 'porter unicode61'
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                client_turn_id TEXT,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending', 'completed', 'failed')),
                direct_answer TEXT,
                archive_context TEXT,
                limitations TEXT,
                insufficient_evidence INTEGER NOT NULL DEFAULT 0,
                citations TEXT,
                retrieval_count INTEGER NOT NULL DEFAULT 0,
                model TEXT,
                error_message TEXT,
                scope_document_ids TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
                ON conversations(updated_at DESC);
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
                ON messages(conversation_id, created_at ASC);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_idempotency
                ON messages(conversation_id, client_turn_id, role)
                WHERE client_turn_id IS NOT NULL;
            """
        )
