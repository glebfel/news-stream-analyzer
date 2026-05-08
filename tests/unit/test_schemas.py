from datetime import datetime

from news_common.models import RawPost, Source


def test_raw_post_serializes_roundtrip():
    p = RawPost(
        id="vk_1",
        source=Source.VK,
        text="hello",
        posted_at=datetime(2026, 1, 1, 12, 0, 0),
    )
    js = p.model_dump(mode="json")
    p2 = RawPost.model_validate(js)
    assert p2 == p


def test_source_enum_values():
    assert Source.VK.value == "vk"
    assert Source.TELEGRAM.value == "telegram"
