from news_common.mocks import fake_batch
from news_common.models import RawPost, Source


class MockPostGenerator:
    def __init__(self, source: Source = Source.VK, batch_size: int = 10) -> None:
        self._source = source
        self._batch_size = batch_size

    def next_batch(self) -> list[RawPost]:
        return fake_batch(self._source, n=self._batch_size)
