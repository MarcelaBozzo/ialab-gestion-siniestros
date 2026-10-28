import os

import pytest

from app.document_processing import process_document


TEST_CLAIM_NUMBER = os.getenv(
    "TEST_CLAIM_NUMBER",
    "CLM-000123",
)

TEST_DOCUMENT_ID = os.getenv("TEST_DOCUMENT_ID")


@pytest.mark.asyncio
async def test_process_document():
    if not TEST_DOCUMENT_ID:
        pytest.skip(
            "TEST_DOCUMENT_ID is not configured"
        )

    result = await process_document(
        claim_number=TEST_CLAIM_NUMBER,
        document_id=TEST_DOCUMENT_ID,
    )

    assert result.claim_number == TEST_CLAIM_NUMBER
    assert result.document_id == TEST_DOCUMENT_ID
    assert len(result.pages) > 0
    assert any(page.strip() for page in result.pages)
