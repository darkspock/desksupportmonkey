class OAuthProviderAlreadyLinkedError(Exception):
    """The OAuth provider ID is already linked to a different user."""

    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"This {provider} account is already linked to another user")


class OAuthProviderNotConfiguredError(Exception):
    """The OAuth provider is not configured on this deployment."""

    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"{provider} login is not configured")
