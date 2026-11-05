import pytest
from pydantic import ValidationError

from app.schemas import (
    CorporateKnowledgeSearchRequest,
    CorporateSourceType,
    CoverageAnalysis,
    CoverageAnalysisRequest,
    CoverageAssessment,
    CoverageEvidence,
    EvidenceReference,
    EvidenceType,
    PolicyAgentHealthResponse,
    SecureCorporateSearchRequest,
)


def coverage_analysis_payload(**overrides):
    payload = {
        "claim_number": "CLM-000123",
        "policy_number": "POL-123456",
        "assessment": "REQUIRES_REVIEW",
        "rationale": "Falta información para concluir.",
        "confidence": 0.5,
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("confidence", [-0.01, 1.01])
def test_coverage_analysis_rejects_confidence_out_of_range(confidence):
    with pytest.raises(ValidationError):
        CoverageAnalysis.model_validate(
            coverage_analysis_payload(confidence=confidence)
        )


@pytest.mark.parametrize("confidence", [0.0, 1.0])
def test_coverage_analysis_accepts_confidence_bounds(confidence):
    analysis = CoverageAnalysis.model_validate(
        coverage_analysis_payload(confidence=confidence)
    )

    assert analysis.confidence == confidence


def test_coverage_analysis_rejects_missing_required_fields():
    with pytest.raises(ValidationError):
        CoverageAnalysis.model_validate({"claim_number": "CLM-000123"})


@pytest.mark.parametrize(
    "assessment",
    [
        CoverageAssessment.POTENTIALLY_COVERED,
        CoverageAssessment.POTENTIALLY_NOT_COVERED,
        CoverageAssessment.REQUIRES_REVIEW,
        CoverageAssessment.INSUFFICIENT_INFORMATION,
    ],
)
def test_coverage_assessment_accepts_only_proposal_values(assessment):
    result = CoverageAnalysis.model_validate(
        coverage_analysis_payload(assessment=assessment)
    )

    assert result.assessment is assessment


@pytest.mark.parametrize("assessment", ["APPROVED", "REJECTED"])
def test_coverage_analysis_rejects_final_decision_values(assessment):
    with pytest.raises(ValidationError):
        CoverageAnalysis.model_validate(
            coverage_analysis_payload(assessment=assessment)
        )


def test_coverage_evidence_rejects_unknown_source_type():
    with pytest.raises(ValidationError):
        CoverageEvidence.model_validate(
            {
                "source_document": "AUTO_STANDARD_2026",
                "source_type": "UNKNOWN_SOURCE",
            }
        )


def test_coverage_evidence_requires_source_document():
    with pytest.raises(ValidationError):
        CoverageEvidence.model_validate(
            {"source_type": CorporateSourceType.POLICY_CONDITIONS}
        )


def test_coverage_request_reuses_existing_claim_and_evidence_contracts():
    evidence = EvidenceReference(
        evidence_type=EvidenceType.CLAIM_DOCUMENT,
        document_id="claim-report",
    )

    request = CoverageAnalysisRequest(
        claim_number="CLM-000123",
        relevant_document_evidence=[evidence],
    )

    assert request.relevant_document_evidence == [evidence]
    assert "session_id" not in request.model_dump()
    assert "messages" not in request.model_dump()


@pytest.mark.parametrize(
    "request_type",
    [CorporateKnowledgeSearchRequest, SecureCorporateSearchRequest],
)
def test_corporate_search_contracts_accept_document_type(request_type):
    request = request_type(
        query="colisión",
        document_type=CorporateSourceType.POLICY_CONDITIONS,
    )

    assert request.document_type is CorporateSourceType.POLICY_CONDITIONS


def test_policy_agent_health_contract_is_typed():
    response = PolicyAgentHealthResponse(
        status="ok",
        agent="policy-agent",
        skills=["analyze_coverage"],
    )

    assert response.skills == ["analyze_coverage"]
