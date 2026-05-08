from unittest.mock import AsyncMock

import pytest
from vk_collector.repositories.cursor import LastSeenCursor


def test_numeric_id_extraction():
    assert LastSeenCursor.numeric_id("vk_ria_1234567") == 1234567
    assert LastSeenCursor.numeric_id("vk_breakingmash_42") == 42
    assert LastSeenCursor.numeric_id("malformed") == 0


@pytest.mark.asyncio
async def test_get_returns_zero_when_missing():
    redis = AsyncMock()
    redis.get.return_value = None
    cursor = LastSeenCursor(redis)
    assert await cursor.get("ria") == 0


@pytest.mark.asyncio
async def test_get_returns_int():
    redis = AsyncMock()
    redis.get.return_value = "1234"
    cursor = LastSeenCursor(redis)
    assert await cursor.get("ria") == 1234


@pytest.mark.asyncio
async def test_set_writes_string():
    redis = AsyncMock()
    cursor = LastSeenCursor(redis)
    await cursor.set("ria", 1234)
    redis.set.assert_called_once_with("vk:last_seen:ria", "1234")
