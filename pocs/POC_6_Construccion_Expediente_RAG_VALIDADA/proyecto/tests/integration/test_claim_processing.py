import os

import pytest

from app.claim_processing import process_claim_documents


TEST_CLAIM_NUMBER = os.getenv(
    "TEST_CLAIM_NUMBER",
    "CLM-000123",
)


@pytest.mark.asyncio
async def test_process_claim_documents():
    result = await process_claim_documents(
        TEST_CLAIM_NUMBER
    )

    assert result.claim_number == TEST_CLAIM_NUMBER
    assert result.claim_data is not None
    assert isinstance(result.evidence, list)
    assert isinstance(result.conflicts, list)
