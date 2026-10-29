from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app import conversation_memory, conversation_service
from app.schemas import (
    ClaimData,
    ClaimsOccurrence,
    Coverage,
    GuardrailDecision,
    Policy,
    PolicySearchResult,
    ProcessedClaimCase,
    RequestClassification,
    VehInfo,
)


async def allow_input(_message, conversation_context=None):
    return GuardrailDecision(
        classification=RequestClassification.IN_SCOPE,
        reason="test",
    )


async def allow_output(_message):
    return GuardrailDecision(
        classification=RequestClassification.IN_SCOPE,
        reason="test",
    )


def claim_data_json(*, policy_number="POL-123456"):
    return ClaimData(
        claim_number="CLM-000123",
        policy_number=policy_number,
        claims_occurrence=ClaimsOccurrence(loss_dt=date(2026, 9, 5)),
        veh_info=VehInfo(vehicle_plate="ABCD12"),
    ).model_dump_json(exclude_none=True)


def current_policy():
    return Policy(
        policy_number="POL-123456",
        policy_status_cd="ACTIVE",
        effective_date=date(2026, 1, 1),
        expiration_date=date(2026, 12, 31),
        insured_vehicle=VehInfo(vehicle_plate="ABCD12"),
        coverages=[
            Coverage(
                coverage_cd="COLLISION",
                coverage_description="Daños por colisión",
                limit_amount=20_000_000,
                deductible_percentage=10,
                minimum_deductible=150_000,
            )
        ],
        source_system="policy_core",
        retrieved_at=datetime(2026, 10, 29, tzinfo=timezone.utc),
    )


@pytest.fixture(autouse=True)
def clear_claim_data_cache():
    conversation_service._claim_data_cache.clear()
    yield
    conversation_service._claim_data_cache.clear()


@pytest.fixture
def conversation_setup(tmp_path, monkeypatch):
    monkeypatch.setattr(
        conversation_memory,
        "CONVERSATION_STORAGE_PATH",
        tmp_path,
    )
    monkeypatch.setattr(conversation_service, "validate_input", allow_input)
    monkeypatch.setattr(conversation_service, "validate_output", allow_output)

    prompts = []

    async def run_agent(prompt):
        prompts.append(prompt)
        return SimpleNamespace(output="Respuesta basada en datos verificados")

    monkeypatch.setattr(conversation_service.agent, "run", run_agent)
    return prompts


@pytest.mark.asyncio
async def test_explicit_policy_number_avoids_duplicate_lookup(
    monkeypatch,
    conversation_setup,
):
    monkeypatch.setattr(
        conversation_service,
        "load_claim_data_json",
        AsyncMock(return_value=claim_data_json()),
    )
    find_policy = AsyncMock()
    get_policy = AsyncMock(return_value=current_policy())
    monkeypatch.setattr(conversation_service, "find_claim_policy", find_policy)
    monkeypatch.setattr(conversation_service, "get_claim_policy", get_policy)
    session = conversation_memory.create_session("CLM-000123")

    response = await conversation_service.process_conversation_turn(
        session.session_id,
        "¿Está vigente la póliza?",
    )

    assert response == "Respuesta basada en datos verificados"
    find_policy.assert_not_awaited()
    get_policy.assert_awaited_once_with("POL-123456")
    prompt = conversation_setup[0]
    assert "<claim_data>" in prompt
    assert "policy_active_on_loss_dt: True" in prompt
    assert "source_system: policy_core" in prompt
    assert "COLLISION: Daños por colisión" in prompt
    assert "does not mean the claim is covered" in " ".join(prompt.split())
    assert "Do not call policy tools again for this turn" in prompt

    persisted = conversation_memory.get_session(session.session_id)
    assert persisted is not None
    assert not hasattr(persisted, "policy")


@pytest.mark.asyncio
async def test_vehicle_lookup_then_get_runs_once_each(
    monkeypatch,
    conversation_setup,
):
    monkeypatch.setattr(
        conversation_service,
        "load_claim_data_json",
        AsyncMock(return_value=claim_data_json(policy_number=None)),
    )
    find_policy = AsyncMock(
        return_value=PolicySearchResult(
            policy_found=True,
            policy_number="POL-123456",
        )
    )
    get_policy = AsyncMock(return_value=current_policy())
    monkeypatch.setattr(conversation_service, "find_claim_policy", find_policy)
    monkeypatch.setattr(conversation_service, "get_claim_policy", get_policy)
    session = conversation_memory.create_session("CLM-000123")

    await conversation_service.process_conversation_turn(
        session.session_id,
        "¿Qué póliza tiene este vehículo?",
    )

    find_policy.assert_awaited_once_with("ABCD12")
    get_policy.assert_awaited_once_with("POL-123456")


@pytest.mark.asyncio
async def test_claim_data_is_cached_but_policy_is_refreshed_each_turn(
    monkeypatch,
    conversation_setup,
):
    claim_data = ClaimData.model_validate_json(claim_data_json())
    process_claim = AsyncMock(
        return_value=ProcessedClaimCase(
            claim_number="CLM-000123",
            claim_data=claim_data,
        )
    )
    get_policy = AsyncMock(return_value=current_policy())
    monkeypatch.setattr(
        conversation_service,
        "process_claim_documents",
        process_claim,
    )
    monkeypatch.setattr(conversation_service, "get_claim_policy", get_policy)
    session = conversation_memory.create_session("CLM-000123")

    await conversation_service.process_conversation_turn(
        session.session_id,
        "¿Cuál es la póliza?",
    )
    await conversation_service.process_conversation_turn(
        session.session_id,
        "¿Sigue vigente?",
    )

    process_claim.assert_awaited_once_with("CLM-000123")
    assert get_policy.await_count == 2
    cached = conversation_service._claim_data_cache["CLM-000123"]
    assert "POL-123456" in cached
    assert "policy_status_cd" not in cached


@pytest.mark.asyncio
async def test_failed_claim_extraction_is_not_cached(monkeypatch):
    process_claim = AsyncMock(side_effect=RuntimeError("extraction failed"))
    monkeypatch.setattr(
        conversation_service,
        "process_claim_documents",
        process_claim,
    )

    assert (
        await conversation_service.load_claim_data_json("CLM-000123")
        is None
    )
    assert (
        await conversation_service.load_claim_data_json("CLM-000123")
        is None
    )

    assert process_claim.await_count == 2
    assert "CLM-000123" not in conversation_service._claim_data_cache
