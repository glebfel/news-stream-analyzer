from processor.services.deduper import Deduper


def test_dedup_detects_near_duplicate():
    d = Deduper(threshold=0.7)
    base = ["президент", "россия", "путин", "встреча", "кремль", "глава"]
    near = ["президент", "россия", "путин", "встреча", "кремль", "глава", "министр"]
    assert d.is_duplicate("p1", base) is False
    assert d.is_duplicate("p2", near) is True


def test_dedup_passes_unrelated():
    d = Deduper(threshold=0.7)
    a = ["москва", "открытие", "технопарк", "студент", "олимпиада"]
    b = ["курс", "доллар", "центральный", "банк", "аналитик", "прогноз"]
    assert d.is_duplicate("a", a) is False
    assert d.is_duplicate("b", b) is False


def test_simhash_is_deterministic():
    h1 = Deduper.simhash_hex(["a", "b", "c"])
    h2 = Deduper.simhash_hex(["a", "b", "c"])
    assert h1 == h2
