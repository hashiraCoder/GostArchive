"""Tests for document text normalization and structure-aware chunking."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.database.connection import connect, initialize_database
from app.ingestion.normalize import chunk_text, normalize_text
from app.services.document_service import rechunk_document

BENCHMARK_SAMPLING_THEOREM = (
    "Aim:\n"
    "To verify the sampling theorem by generating an original signal, "
    "sampling it at different sampling frequencies, and reconstructing the signal using MATLAB.\n\n"
    "Theory:\n"
    "The sampling theorem states that a continuous-time signal can be reconstructed "
    "exactly from its sampled values if the sampling frequency is greater than or equal "
    "to twice the highest frequency present in the signal.\n\n"
    "fs\u200b\u22652fm\u200b\n\n"
    "where:\n"
    "fs is the sampling frequency\n"
    "fm is the maximum frequency of the message signal\n\n"
    "clc;\n"
    "clear;\n"
    "close all;\n\n"
    "% Message signal frequency\n"
    "fm = 5;\n\n"
    "% Time vector for original continuous signal\n"
    "t = 0:0.001:1;\n\n"
    "% Original signal\n"
    "x = sin(2*pi*fm*t);\n\n"
    "% Sampling frequency greater than Nyquist rate\n"
    "fs = 20;\n\n"
    "% Sampled time vector\n"
    "ts = 0:1/fs:1;\n\n"
    "% Sampled signal\n"
    "xs = sin(2*pi*fm*ts);\n\n"
    "% Reconstruct the signal using interpolation\n"
    "tr = 0:0.001:1;\n"
    "xr = interp1(ts, xs, tr, 'spline');\n\n"
    "% Plot original signal\n"
    "subplot(3,1,1);\n"
    "plot(t, x, 'b', 'LineWidth', 1.5);\n"
    "title('Original Signal');\n"
    "xlabel('Time');\n"
    "ylabel('Amplitude');\n"
    "grid on;\n\n"
    "% Plot sampled signal\n"
    "subplot(3,1,2);\n"
    "stem(ts, xs, 'r', 'filled');\n"
    "title('Sampled Signal');\n"
    "xlabel('Time');\n"
    "ylabel('Amplitude');\n"
    "grid on;\n\n"
    "% Plot reconstructed signal\n"
    "subplot(3,1,3);\n"
    "plot(tr, xr, 'k', 'LineWidth', 1.5);\n"
    "title('Reconstructed Signal');\n"
    "xlabel('Time');\n"
    "ylabel('Amplitude');\n"
    "grid on;\n\n"
    "and alternative\n\n"
    "clc;\n"
    "clear;\n"
    "close all;\n\n"
    "fm=5; fs=20;\n"
    "t=0:0.001:1;\n"
    "x=sin(2*pi*fm*t);\n\n"
    "n=0:1/fs:1;\n"
    "xs=sin(2*pi*fm*n);\n\n"
    "xr=interp1(n,xs,t,'linear');\n\n"
    "subplot(3,1,1);\n"
    "plot(t,x);\n"
    "title('Original Signal');\n"
    "grid on;\n\n"
    "subplot(3,1,2);\n"
    "stem(n,xs);\n"
    "title('Sampled Signal');\n"
    "grid on;\n\n"
    "subplot(3,1,3);\n"
    "plot(t,xr);\n"
    "title('Reconstructed Signal');\n"
    "grid on;\n"
)


def test_normalize_strips_zero_width_and_invisible_chars() -> None:
    raw = "Signal\u200b\u200cwith\u200dinvisible\ufeffformatting\u2060chars\u00adhere."
    cleaned = normalize_text(raw)
    assert cleaned == "Signalwithinvisibleformattingcharshere."
    assert "\u200b" not in cleaned
    assert "\ufeff" not in cleaned


def test_normalize_converts_math_inequalities_and_operators() -> None:
    raw = (
        "Conditions: fs\u22652fm and f\u226410 and x\u2260y and a\u2248b "
        "and 5\u22123=2 and 3\u00d74=12 and 12\u00f74=3."
    )
    normalized = normalize_text(raw)
    assert "fs >= 2fm" in normalized
    assert "f <= 10" in normalized
    assert "x != y" in normalized
    assert "a ~= b" in normalized
    assert "5-3=2" in normalized
    assert "3*4=12" in normalized
    assert "12/4=3" in normalized


def test_normalize_converts_smart_quotes_and_typography() -> None:
    raw = "\u201cHello\u201d and \u2018world\u2019 with\u00a0non-breaking space."
    normalized = normalize_text(raw)
    assert normalized == "\"Hello\" and 'world' with non-breaking space."


def test_chunk_text_empty_and_invalid_arguments() -> None:
    assert chunk_text("") == []
    with pytest.raises(ValueError, match="target_size must be greater than overlap"):
        chunk_text("Some text", target_size=100, overlap=100)


def test_chunk_text_structure_aware_sampling_theorem() -> None:
    """Benchmark test verifying structural preservation on sampling theorem document."""
    normalized = normalize_text(BENCHMARK_SAMPLING_THEOREM)
    chunks = chunk_text(normalized)

    # Must produce exactly 3 coherent chunks
    assert len(chunks) == 3

    chunk0 = chunks[0].content
    chunk1 = chunks[1].content
    chunk2 = chunks[2].content

    # Chunk 0: Theoretical formulation and Aim
    assert "Aim:" in chunk0
    assert "Theory:" in chunk0
    assert "fs >= 2fm" in chunk0
    assert "where:" in chunk0
    assert "fs is the sampling frequency" in chunk0
    assert "fm is the maximum frequency" in chunk0
    # Code must not leak into theory chunk
    assert "clc;" not in chunk0

    # Chunk 1: Full Implementation 1
    assert "clc;" in chunk1
    assert "clear;" in chunk1
    assert "close all;" in chunk1
    assert "fm = 5;" in chunk1
    assert "t = 0:0.001:1;" in chunk1
    assert "xr = interp1(ts, xs, tr, 'spline');" in chunk1
    assert "% Plot original signal" in chunk1
    assert "% Plot sampled signal" in chunk1
    assert "% Plot reconstructed signal" in chunk1
    assert "stem(ts, xs, 'r', 'filled');" in chunk1
    assert "title('Reconstructed Signal');" in chunk1
    # Alternative implementation must not be in Chunk 1
    assert "and alternative" not in chunk1
    assert "'linear'" not in chunk1

    # Chunk 2: Full Alternative Implementation
    assert "and alternative" in chunk2
    assert "fm=5; fs=20;" in chunk2
    assert "xr=interp1(n,xs,t,'linear');" in chunk2
    assert "stem(n,xs);" in chunk2


def test_chunk_text_source_offsets_valid() -> None:
    """Verify that source offsets accurately correspond to chunk content."""
    normalized = normalize_text(BENCHMARK_SAMPLING_THEOREM)
    chunks = chunk_text(normalized)
    for chunk in chunks:
        assert chunk.start_char < chunk.end_char
        extracted = normalized[chunk.start_char : chunk.end_char].strip()
        assert extracted == chunk.content


def test_chunk_text_long_paragraph_window_slicing() -> None:
    """Oversized continuous prose splits cleanly across sentence boundaries."""
    sentence = "GhostArchive preserves evidence locally without cloud transmission. "
    long_text = sentence * 30  # ~2040 characters
    chunks = chunk_text(long_text, target_size=900, overlap=120)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk.content) <= 900
        # Check that chunk ends on a sentence boundary or word boundary
        assert chunk.content.endswith(".") or chunk.content[-1].isalnum()


def test_rechunk_document_updates_database(temp_settings: Settings) -> None:
    """Verify rechunk_document updates SQLite chunks, FTS5 index, and document status."""
    initialize_database(temp_settings)
    doc_id = "doc-sampling-test"
    stored_name = "test_sampling.txt"
    temp_settings.files_dir.mkdir(parents=True, exist_ok=True)
    file_path = temp_settings.files_dir / stored_name
    file_path.write_text(BENCHMARK_SAMPLING_THEOREM, encoding="utf-8")

    with connect(temp_settings) as conn:
        conn.execute(
            """
            INSERT INTO documents (
                id, original_filename, stored_filename, content_hash, file_type,
                byte_size, status, created_at, updated_at
            ) VALUES (?, ?, ?, 'dummy_hash', 'txt', ?, 'ready', datetime('now'), datetime('now'))
            """,
            (doc_id, "sampling theorem.txt", stored_name, len(BENCHMARK_SAMPLING_THEOREM)),
        )

    class MockProvider:
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [[0.1] * 4 for _ in texts]

    class MockStore:
        def __init__(self) -> None:
            self.deleted: list[str] = []
            self.upserted: list[str] = []

        def delete(self, ids: list[str]) -> None:
            self.deleted.extend(ids)

        def upsert(self, ids, embeddings, documents, metadatas) -> None:
            self.upserted.extend(ids)

    mock_store = MockStore()
    res = rechunk_document(
        temp_settings,
        doc_id,
        embedding_provider=MockProvider(),
        vector_store=mock_store,
    )

    assert res["status"] == "ready"
    assert res["chunk_count"] == 3
    assert len(mock_store.upserted) == 3

    with connect(temp_settings) as conn:
        chunks = conn.execute(
            """
            SELECT chunk_index, content
            FROM document_chunks
            WHERE document_id = ?
            ORDER BY chunk_index
            """,
            (doc_id,),
        ).fetchall()
        assert len(chunks) == 3
        assert "Aim:" in chunks[0]["content"]
        assert "interp1(ts, xs, tr, 'spline')" in chunks[1]["content"]
        assert "interp1(n,xs,t,'linear')" in chunks[2]["content"]

        # Verify FTS5 is updated
        fts_rows = conn.execute(
            "SELECT count(*) FROM document_chunks_fts WHERE document_id = ?",
            (doc_id,),
        ).fetchone()[0]
        assert fts_rows == 3
