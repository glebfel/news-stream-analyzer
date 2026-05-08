import asyncio

import pytest
from vk_collector.clients.token_pool import TokenPool


@pytest.mark.asyncio
async def test_pool_round_robins():
    pool = TokenPool(["a", "b", "c"])
    assert [await pool.next() for _ in range(7)] == ["a", "b", "c", "a", "b", "c", "a"]


@pytest.mark.asyncio
async def test_pool_single_token():
    pool = TokenPool(["only"])
    assert await pool.next() == "only"
    assert await pool.next() == "only"


def test_pool_rejects_empty():
    with pytest.raises(ValueError):
        TokenPool([])


@pytest.mark.asyncio
async def test_pool_concurrent_safe():
    pool = TokenPool(["a", "b", "c", "d"])
    results = await asyncio.gather(*[pool.next() for _ in range(40)])
    assert sorted(results) == sorted(["a", "b", "c", "d"] * 10)
