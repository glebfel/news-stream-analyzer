from datasketch import MinHash, MinHashLSH


class Deduper:
    def __init__(self, threshold: float = 0.85, num_perm: int = 128) -> None:
        self._lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        self._num_perm = num_perm
        self._seen_ids: set[str] = set()

    def is_duplicate(self, post_id: str, tokens: list[str]) -> bool:
        if post_id in self._seen_ids:
            return True
        sig = self._signature(tokens)
        if self._lsh.query(sig):
            return True
        self._lsh.insert(post_id, sig)
        self._seen_ids.add(post_id)
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
