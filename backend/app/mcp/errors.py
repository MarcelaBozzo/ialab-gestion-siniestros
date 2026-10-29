class McpError(RuntimeError):
    pass
class McpUnavailable(McpError):
    pass
class McpToolNotFound(McpError):
    pass
class McpToolExecutionError(McpError):
    pass
class McpInvalidResponse(McpError):
    pass
class McpCustomerApiUnavailable(McpError):
    pass
class McpCustomerApiError(McpError):
    pass
class McpCustomerNotFound(McpError):
    pass


class McpPolicyApiUnavailable(McpError):
    pass


class McpPolicyApiError(McpError):
    pass


class McpPolicyNotFound(McpError):
    pass
