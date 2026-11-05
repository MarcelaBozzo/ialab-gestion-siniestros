import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app import conversation_memory, conversation_service, coverage_service
from app.agents import claims_agent
from app.schemas import (
    CoverageAnalysis,
    CoverageAssessment,
    GuardrailDecision,
    RequestClassification,
)


async def allow(_value, conversation_context=None):
    return GuardrailDecision(
        classification=RequestClassification.IN_SCOPE,
        reason="test",
    )


@pytest.mark.asyncio
async def test_sessions_are_isolated_and_same_claim_can_be_reanalyzed(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(conversation_memory, "CONVERSATION_STORAGE_PATH", tmp_path)
    monkeypatch.setattr(conversation_service, "validate_input", allow)
    monkeypatch.setattr(conversation_service, "validate_output", allow)
    monkeypatch.setattr(
        conversation_service,
        "resolve_policy_number",
        AsyncMock(return_value=None),
    )

    async def claim_data(claim_number):
        return json.dumps(
            {
                "claim_number": claim_number,
                "policy_number": "POL-123456",
                "veh_info": {"vehicle_plate": "ABCD12"},
            }
        )

    monkeypatch.setattr(conversation_service, "load_claim_data_json", claim_data)
    calls = []

    async def remote_analysis(request):
        calls.append(request)
        return CoverageAnalysis(
            claim_number=request.claim_number,
            policy_number=request.policy_number,
            assessment=CoverageAssessment.REQUIRES_REVIEW,
            rationale=f"Propuesta remota {len(calls)}",
            confidence=0.5,
        )

    monkeypatch.setattr(
        coverage_service.policy_a2a_client,
        "analyze_coverage",
        remote_analysis,
    )
    prompts = []

    async def delegated_run(prompt, deps=None):
        prompts.append(prompt)
        analysis = await claims_agent.analyze_coverage(
            SimpleNamespace(deps=deps)
        )
        return SimpleNamespace(output=analysis.rationale)

    monkeypatch.setattr(conversation_service.agent, "run", delegated_run)

    first = conversation_memory.create_session("CLM-000123")
    second = conversation_memory.create_session("CLM-000999")
    await conversation_service.process_conversation_turn(
        first.session_id,
        "Analiza la cobertura",
    )
    await conversation_service.process_conversation_turn(
        first.session_id,
        "Reanaliza el mismo siniestro",
    )
    await conversation_service.process_conversation_turn(
        second.session_id,
        "Analiza la cobertura",
    )

    assert [request.claim_number for request in calls] == [
        "CLM-000123",
        "CLM-000123",
        "CLM-000999",
    ]
    assert "Propuesta remota 1" in prompts[1]
    assert "Propuesta remota 1" not in prompts[2]
    assert all(
        not (
            {"session_id", "messages", "summary"}
            & request.model_dump().keys()
        )
        for request in calls
    )
    assert len(conversation_memory.get_session(first.session_id).messages) == 4
    assert len(conversation_memory.get_session(second.session_id).messages) == 2
