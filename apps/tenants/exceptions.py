class TenantNotFoundError(Exception):
    """Raised when a tenant cannot be resolved from the request host."""


class TenantInactiveError(Exception):
    """Raised when the resolved tenant exists but is inactive."""


class DemoLimitReachedError(Exception):
    """Raised when an IP has hit its daily demo-creation limit."""
