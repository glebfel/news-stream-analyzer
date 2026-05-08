class VKError(Exception):
    """Base class for VK API errors."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"VK error {code}: {message}")
        self.code = code
        self.message = message


class VKAuthError(VKError):
    """Token is invalid or expired (codes 5, 17)."""


class VKRateLimitError(VKError):
    """Too many requests per second (code 6) — retryable."""


class VKCaptchaError(VKError):
    """Captcha required (code 14) — cannot be solved automatically."""


class VKTransientError(VKError):
    """Internal server error or timeout (codes 1, 10) — retryable."""


class VKPermanentError(VKError):
    """Client-side errors not worth retrying."""


def from_vk_response(error: dict) -> VKError:
    code = error.get("error_code", 0)
    msg = error.get("error_msg", "")
    if code in (5, 17, 27, 28):
        return VKAuthError(code, msg)
    if code == 6:
        return VKRateLimitError(code, msg)
    if code == 14:
        return VKCaptchaError(code, msg)
    if code in (1, 10):
        return VKTransientError(code, msg)
    return VKPermanentError(code, msg)
