from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.agents import claims_agent
from app.schemas import (
    ClaimData,
    CoverageAnalysis,
    CoverageAssessment,
)


def make_dependencies():
    return claims_agent.ClaimsAgentDependencies(
        claim_number="CLM-000123",
        claim_data=ClaimData(
            claim_number="CLM-000123",
            policy_number="POL-123456",
        ),
        relevant_document_evidence=[],
    )


def test_claims_agent_preserves_tools_and_registers_typed_delegation():
    assert claims_agent.agent.deps_type is claims_agent.ClaimsAgentDependencies
    assert set(claims_agent.agent._function_toolset.tools) == {
        "calculate_deductible",
        "calculate_reserve",
        "get_missing_claim_information",
        "verify_customer_tool",
        "get_customer_profile_tool",
        "find_policy_tool",
        "get_policy_tool",
        "analyze_coverage",
    }


@pytest.mark.asyncio
async def test_analyze_coverage_uses_trusted_dependencies(monkeypatch):
    expected = CoverageAnalysis(
        claim_number="CLM-000123",
        policy_number="POL-123456",
        assessment=CoverageAssessment.REQUIRES_REVIEW,
        rationale="Propuesta para revisión.",
        confidence=0.4,
    )
    delegate = AsyncMock(return_value=expected)
    monkeypatch.setattr(claims_agent, "analyze_claim_coverage", delegate)

    result = await claims_agent.analyze_coverage(
        SimpleNamespace(deps=make_dependencies())
    )

    assert result is expected
    request = delegate.await_args.args[0]
    assert request.claim_number == "CLM-000123"
    assert request.policy_number == "POL-123456"
    assert "session_id" not in request.model_dump()
    assert "messages" not in request.model_dump()


@pytest.mark.parametrize(
    "dependencies",
    [
        None,
        claims_agent.ClaimsAgentDependencies(
            claim_number=None,
            claim_data=None,
            relevant_document_evidence=[],
        ),
    ],
)
@pytest.mark.asyncio
async def test_analyze_coverage_requires_active_claim_data(dependencies):
    with pytest.raises(ValueError, match="active claim and ClaimData"):
        await claims_agent.analyze_coverage(
            SimpleNamespace(deps=dependencies)
        )


def test_claims_agent_prompt_requires_policy_agent_delegation():
    prompts = " ".join(claims_agent.agent._system_prompts)

    assert "delega el análisis al Policy Agent" in prompts
    assert "No realices por tu cuenta" in prompts
    assert "No envíes ConversationSession" in prompts
    assert "No inventes ni sustituyas su análisis" in prompts
