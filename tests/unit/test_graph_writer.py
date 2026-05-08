from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from graph_builder.services.graph_writer import GraphWriterService


def make_payload(post_id: str, entities: int, relations: int) -> dict:
    return {
        "post": {"id": post_id, "posted_at": datetime.utcnow().isoformat()},
        "sentiment": {"label": "positive", "score": 0.8},
        "entities": [
            {"text": f"Entity{i}", "type": "ORG", "wikidata_id": None} for i in range(entities)
        ],
        "relations": [
            {
                "head": f"Entity{i}",
                "head_type": "ORG",
                "tail": f"Entity{i + 1}",
                "tail_type": "ORG",
            }
            for i in range(relations)
        ],
    }


@pytest.mark.asyncio
async def test_buffers_until_threshold():
    repo = AsyncMock()
    writer = GraphWriterService(repo, flush_every=10, flush_seconds=99999)

    # 5 entities — below threshold, no flush yet
    await writer.write_payload(make_payload("p1", entities=5, relations=0))
    repo.upsert_entities_batch.assert_not_called()

    # +6 entities — total 11, exceeds threshold, flush fires
    await writer.write_payload(make_payload("p2", entities=6, relations=0))
    repo.upsert_entities_batch.assert_called_once()
    args = repo.upsert_entities_batch.call_args.args[0]
    assert len(args) == 11


@pytest.mark.asyncio
async def test_flush_clears_buffer():
    repo = AsyncMock()
    writer = GraphWriterService(repo, flush_every=5, flush_seconds=99999)

    await writer.write_payload(make_payload("p1", entities=5, relations=3))
    repo.upsert_entities_batch.assert_called_once()
    repo.upsert_relations_batch.assert_called_once()

    # second payload should start fresh
    repo.reset_mock()
    await writer.write_payload(make_payload("p2", entities=2, relations=0))
    repo.upsert_entities_batch.assert_not_called()


@pytest.mark.asyncio
async def test_explicit_flush_drains_buffer():
    repo = AsyncMock()
    writer = GraphWriterService(repo, flush_every=999, flush_seconds=99999)

    await writer.write_payload(make_payload("p1", entities=3, relations=2))
    repo.upsert_entities_batch.assert_not_called()

    await writer.flush()
    repo.upsert_entities_batch.assert_called_once()
    repo.upsert_relations_batch.assert_called_once()


@pytest.mark.asyncio
async def test_empty_flush_is_noop():
    repo = AsyncMock()
    writer = GraphWriterService(repo, flush_every=10, flush_seconds=99999)
    await writer.flush()
    repo.upsert_entities_batch.assert_not_called()
    repo.upsert_relations_batch.assert_not_called()
