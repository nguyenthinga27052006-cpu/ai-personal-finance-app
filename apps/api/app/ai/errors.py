class AIError(Exception):
    """Base error for controlled AI platform failures."""


class AuthenticationContextError(AIError):
    pass


class AuthorizationError(AIError):
    pass


class GuardrailViolation(AIError):
    pass


class ToolNotAllowedError(AIError):
    pass


class ToolExecutionError(AIError):
    pass


class ProviderTimeoutError(AIError):
    pass


class ProviderUnavailableError(AIError):
    pass


class ProviderResponseError(AIError):
    pass


class StructuredOutputError(AIError):
    pass


class InsufficientDataError(AIError):
    pass


class WriteToolsDisabledError(AIError):
    pass
