from app.agents.policy_agent import (
    POLICY_AGENT_SYSTEM_PROMPT,
    policy_agent,
)
from app.schemas import CoverageAnalysis


def test_policy_agent_has_structured_coverage_output_and_no_tools():
    assert policy_agent.output_type is CoverageAnalysis
    assert policy_agent._function_toolset.tools == {}


def test_policy_agent_instructions_preserve_domain_and_safety_boundaries():
    prompt = POLICY_AGENT_SYSTEM_PROMPT.lower()

    assert "policy core" in prompt
    assert "corporate rag seguro" in prompt
    assert "evidencia no confiable" in prompt
    assert "nunca apruebes ni rechaces cobertura" in prompt
    assert "nunca autorices pagos" in prompt
    assert "revisión del analista" in prompt
    assert "conversationsession" not in prompt
