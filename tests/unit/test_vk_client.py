import asyncio
import time

import pytest
from vk_collector.clients.exceptions import (
    VKAuthError,
    VKCaptchaError,
    VKPermanentError,
    VKRateLimitError,
    VKTransientError,
    from_vk_response,
)
from vk_collector.clients.rate_limiter import AsyncRateLimiter


def test_error_mapping_auth():
    err = from_vk_response({"error_code": 5, "error_msg": "auth failed"})
    assert isinstance(err, VKAuthError)


def test_error_mapping_rate_limit():
    err = from_vk_response({"error_code": 6, "error_msg": "too many requests"})
    assert isinstance(err, VKRateLimitError)


def test_error_mapping_captcha():
    err = from_vk_response({"error_code": 14, "error_msg": "captcha needed"})
    assert isinstance(err, VKCaptchaError)


def test_error_mapping_transient():
    err = from_vk_response({"error_code": 10, "error_msg": "internal"})
    assert isinstance(err, VKTransientError)


def test_error_mapping_permanent():
    err = from_vk_response({"error_code": 100, "error_msg": "param invalid"})
    assert isinstance(err, VKPermanentError)


@pytest.mark.asyncio
async def test_rate_limiter_throttles():
    limiter = AsyncRateLimiter(rate=10.0)
    start = time.monotonic()
    for _ in range(5):
        await limiter.acquire()
    elapsed = time.monotonic() - start
    assert elapsed >= 0.4


@pytest.mark.asyncio
async def test_rate_limiter_concurrent_calls_serialised():
    limiter = AsyncRateLimiter(rate=20.0)

    async def call() -> None:
        await limiter.acquire()

    start = time.monotonic()
    await asyncio.gather(*[call() for _ in range(10)])
    assert time.monotonic() - start >= 0.45
