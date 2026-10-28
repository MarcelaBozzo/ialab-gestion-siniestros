from app.vector_store import create_chunk_point_id


def test_chunk_point_id_is_deterministic():
    first = create_chunk_point_id("DOC-001", 0)
    second = create_chunk_point_id("DOC-001", 0)
    assert first == second


def test_different_chunks_have_different_ids():
    first = create_chunk_point_id("DOC-001", 0)
    second = create_chunk_point_id("DOC-001", 1)
    assert first != second
