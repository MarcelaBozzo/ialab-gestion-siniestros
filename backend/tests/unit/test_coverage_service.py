from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app import coverage_service
from app.a2a.errors import A2AAgentUnavailable, A2AInvalidResponse
from app.schemas import (
    ClaimData,
    ClaimsOccurrence,
    ConversationMessage,
    ConversationSession,
    CoverageAnalysis,
    CoverageAnalysisRequest,
    CoverageAssessment,
    EvidenceReference,
    EvidenceType,
    VehInfo,
)


def make_claim_data() -> ClaimData:
    return ClaimData(
        claim_number="CLM-000123",
        policy_number="POL-123456",
        claims_occurrence=ClaimsOccurrence(
            loss_dt=date(2026, 7, 2),
            loss_desc="Colisión con otro vehículo.",
        ),
        veh_info=VehInfo(vehicle_plate="ABCD12"),
    )


def make_request() -> CoverageAnalysisRequest:
    return coverage_service.build_coverage_analysis_request(
        claim_number="CLM-000123",
        claim_data=make_claim_data(),
    )


def make_analysis(**updates) -> CoverageAnalysis:
    values = {
        "claim_number": "CLM-000123",
        "policy_number": "POL-123456",
        "assessment": CoverageAssessment.REQUIRES_REVIEW,
        "rationale": "Propuesta sujeta a revisión.",
        "confidence": 0.4,
    }
    values.update(updates)
    return CoverageAnalysis(**values)


def test_build_request_maps_only_claim_data_and_selected_evidence():
    selected_evidence = [
        EvidenceReference(
            evidence_type=EvidenceType.CLAIM_DOCUMENT,
            document_id="claim-report",
            document_type="CLAIM_REPORT",
            page=2,
            chunk_index=3,
            claim_number="CLM-000123",
            content="Impacto frontal.",
        )
    ]

    request = coverage_service.build_coverage_analysis_request(
        claim_number=" CLM-000123 ",
        claim_data=make_claim_data(),
        relevant_document_evidence=selected_evidence,
    )

    assert request.claim_number == "CLM-000123"
    assert request.policy_number == "POL-123456"
    assert request.claims_occurrence.loss_dt == date(2026, 7, 2)
    assert request.veh_info.vehicle_plate == "ABCD12"
    assert request.relevant_document_evidence == selected_evidence
    fields = request.model_dump()
    assert "session_id" not in fields
    assert "messages" not in fields
    assert "customer_profile" not in fields


@pytest.mark.parametrize("claim_number", ["", "   "])
def test_build_request_rejects_empty_claim_number(claim_number):
    with pytest.raises(ValueError, match="claim_number cannot be empty"):
        coverage_service.build_coverage_analysis_request(
            claim_number=claim_number,
            claim_data=make_claim_data(),
        )


def test_build_request_rejects_claim_number_mismatch():
    with pytest.raises(
        ValueError,
        match="claim_number does not match ClaimData",
    ):
        coverage_service.build_coverage_analysis_request(
            claim_number="CLM-999999",
            claim_data=make_claim_data(),
        )


def test_build_request_does_not_copy_conversation_session():
    now = datetime.now(timezone.utc)
    session = ConversationSession(
        session_id="SESSION-A",
        claim_number="CLM-000123",
        created_at=now,
        updated_at=now,
        summary="Resumen privado.",
        messages=[
            ConversationMessage(
                role="user",
                content="¿Tiene cobertura?",
                created_at=now,
            )
        ],
    )

    request = coverage_service.build_coverage_analysis_request(
        claim_number=session.claim_number,
        claim_data=make_claim_data(),
    )

    assert set(request.model_dump()) == {
        "claim_number",
        "policy_number",
        "claims_occurrence",
        "veh_info",
        "relevant_document_evidence",
    }


@pytest.mark.asyncio
async def test_analyze_claim_coverage_delegates_and_validates_identity(
    monkeypatch,
):
    request = make_request()
    expected = make_analysis()
    call = AsyncMock(return_value=expected)
    monkeypatch.setattr(
        coverage_service.policy_a2a_client,
        "analyze_coverage",
        call,
    )

    result = await coverage_service.analyze_claim_coverage(request)

    assert result is expected
    call.assert_awaited_once_with(request)


@pytest.mark.parametrize(
    "analysis",
    [
        make_analysis(claim_number="CLM-OTHER"),
        make_analysis(policy_number="POL-OTHER"),
    ],
)
@pytest.mark.asyncio
async def test_analyze_claim_coverage_rejects_mismatched_identity(
    monkeypatch,
    analysis,
):
    monkeypatch.setattr(
        coverage_service.policy_a2a_client,
        "analyze_coverage",
        AsyncMock(return_value=analysis),
    )

    with pytest.raises(A2AInvalidResponse):
        await coverage_service.analyze_claim_coverage(make_request())


@pytest.mark.asyncio
async def test_analyze_claim_coverage_preserves_a2a_error(monkeypatch):
    monkeypatch.setattr(
        coverage_service.policy_a2a_client,
        "analyze_coverage",
        AsyncMock(side_effect=A2AAgentUnavailable("unavailable")),
    )

    with pytest.raises(A2AAgentUnavailable):
        await coverage_service.analyze_claim_coverage(make_request())
