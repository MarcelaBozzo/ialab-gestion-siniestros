import pytest

from app.chunking import chunk_text


def test_chunk_text_empty():
    assert chunk_text("") == []


def test_chunk_text_smaller_than_chunk():
    text = "Texto corto"
    result = chunk_text(
        text,
        chunk_size=100,
        overlap=10,
    )
    assert result == ["Texto corto"]


def test_chunk_text_creates_multiple_chunks():
    text = "0123456789" "ABCDEFGHIJ"
    result = chunk_text(
        text,
        chunk_size=10,
        overlap=2,
    )
    assert len(result) > 1


def test_chunk_text_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text(
            "texto",
            chunk_size=10,
            overlap=10,
        )
