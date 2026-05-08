from news_common.mocks import fake_batch
from news_common.models import RawPost, Source


class MockPostGenerator:
    def __init__(self, batch_size: int = 8) -> None:
        self._batch_size = batch_size

    def next_batch(self) -> list[RawPost]:
        return fake_batch(Source.TELEGRAM, n=self._batch_size)
