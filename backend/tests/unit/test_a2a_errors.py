from app.a2a.errors import (
    A2AAgentUnavailable,
    A2ACapabilityNotFound,
    A2AError,
    A2AInvalidResponse,
    A2ARemoteTaskFailed,
)


def test_a2a_errors_share_domain_hierarchy():
    errors = [
        A2AAgentUnavailable(),
        A2ACapabilityNotFound(),
        A2AInvalidResponse(),
        A2ARemoteTaskFailed(),
    ]

    assert all(isinstance(error, A2AError) for error in errors)
