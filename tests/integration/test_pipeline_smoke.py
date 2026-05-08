import pytest
from news_common import Source
from news_common.mocks import fake_batch
from processor.services.deduper import Deduper
from processor.services.normalizer import Normalizer


@pytest.mark.parametrize("source", [Source.VK, Source.TELEGRAM])
def test_normalize_then_dedup_handles_batch(source: Source):
    posts = fake_batch(source, n=20)
    normalizer = Normalizer()
    deduper = Deduper(threshold=0.85)
    accepted = 0
    for p in posts:
        cleaned = normalizer.clean(p.text)
        _, lemmas = normalizer.tokenize(cleaned)
        if not deduper.is_duplicate(p.id, lemmas):
            accepted += 1
    assert accepted >= 1
    assert accepted <= len(posts)
