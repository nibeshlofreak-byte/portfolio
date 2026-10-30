"""Authentication and database errors shared by the API and app client."""


class AuthStoreError(Exception):
    """An expected registration, login, or database configuration error."""


class AuthValidationError(AuthStoreError):
    """User input or credentials were rejected."""


class AuthDatabaseError(AuthStoreError):
    """MySQL could not complete the requested operation."""
