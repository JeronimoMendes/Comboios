class ComboiosError(Exception):
    """Base exception for comboios."""


class AuthenticationError(ComboiosError):
    """Failed to fetch or refresh credentials."""


class APIError(ComboiosError):
    """API returned an error response."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class NotFoundError(APIError):
    """Resource not found (404)."""

    def __init__(self, message: str = "Not found") -> None:
        super().__init__(message, status_code=404)
