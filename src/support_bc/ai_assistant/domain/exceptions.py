class AIProviderError(Exception):
    """A single AI provider call failed."""
    pass


class AIRateLimitExceededError(Exception):
    """User exceeded the AI query rate limit."""
    pass


class AIUnavailableError(Exception):
    """All AI providers failed."""
    pass
