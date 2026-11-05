class A2AError(RuntimeError):
    pass


class A2AAgentUnavailable(A2AError):
    pass


class A2AInvalidResponse(A2AError):
    pass


class A2ARemoteTaskFailed(A2AError):
    pass


class A2ACapabilityNotFound(A2AError):
    pass
