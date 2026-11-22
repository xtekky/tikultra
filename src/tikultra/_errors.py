from __future__ import annotations

from typing import Any


class TikUltraError(Exception):
    def __init__(
        self,
        message:     str,
        *,
        status_code: int            = 0,
        code:        str            = 'unknown_error',
        request_id:  str            = '',
        credits_cost: int           = 0,
        body:        dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message      = message
        self.status_code  = status_code
        self.code         = code
        self.request_id   = request_id
        self.credits_cost = credits_cost
        self.body         = body if body is not None else {}


class BadRequestError(TikUltraError):
    pass


class AuthenticationError(TikUltraError):
    pass


class InsufficientCreditsError(TikUltraError):
    pass


class PermissionDeniedError(TikUltraError):
    pass


class NotFoundError(TikUltraError):
    pass


class RateLimitError(TikUltraError):
    def __init__(
        self,
        message:      str,
        *,
        retry_after:  float | None = None,
        status_code:  int          = 429,
        code:         str          = 'rate_limited',
        request_id:   str          = '',
        credits_cost: int          = 0,
        body:         dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            status_code  = status_code,
            code         = code,
            request_id   = request_id,
            credits_cost = credits_cost,
            body         = body,
        )
        self.retry_after = retry_after


class UpstreamError(TikUltraError):
    pass
