from urllib.parse import urlparse

from datasketch import MinHash, MinHashLSH


class Deduper:
    """Streaming near-duplicate detector based on MinHash + LSH.

    By default uses an in-memory LSH index (suitable for tests and local dev).
    When `redis_url` is provided, the LSH index is backed by Redis through
    `datasketch`'s built-in storage layer; this makes the dedup state
    persistent across processor restarts and shareable between replicas.
    """

    def __init__(
        self,
        threshold: float = 0.85,
        num_perm: int = 128,
        redis_url: str | None = None,
        namespace: str = "dedup",
    ) -> None:
        self._num_perm = num_perm
        if redis_url:
            parsed = urlparse(redis_url)
            self._lsh = MinHashLSH(
                threshold=threshold,
                num_perm=num_perm,
                storage_config={
                    "type": "redis",
                    "basename": namespace.encode(),
                    "redis": {
                        "host": parsed.hostname or "localhost",
                        "port": parsed.port or 6379,
                        "db": int(parsed.path.lstrip("/")) if parsed.path else 0,
                    },
                },
            )
            self._persistent = True
        else:
            self._lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
            self._persistent = False

    def is_duplicate(self, post_id: str, tokens: list[str]) -> bool:
        if self._lsh.__contains__(post_id):
            return True
        sig = self._signature(tokens)
        if self._lsh.query(sig):
            return True
        self._lsh.insert(post_id, sig)
        return False

    def signature(self, tokens: list[str]) -> MinHash:
        return self._signature(tokens)

    def _signature(self, tokens: list[str]) -> MinHash:
        m = MinHash(num_perm=self._num_perm)
        for sh in self._shingles(tokens):
            m.update(sh)
        return m

    @staticmethod
    def _shingles(tokens: list[str], k: int = 3) -> list[bytes]:
        if len(tokens) < k:
            return [(" ".join(tokens)).encode()]
        return [(" ".join(tokens[i : i + k])).encode() for i in range(len(tokens) - k + 1)]

    @staticmethod
    def simhash_hex(tokens: list[str], num_perm: int = 64) -> str:
        m = MinHash(num_perm=num_perm)
        for t in tokens:
            m.update(t.encode())
        return m.digest().tobytes().hex()
