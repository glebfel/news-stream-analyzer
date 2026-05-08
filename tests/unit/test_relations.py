from news_common.models import Entity, EntityType
from nlp_worker.services.relations import WINDOW_WEIGHTS, RelationExtractorService


def _ent(text: str, etype: EntityType, start: int, end: int) -> Entity:
    return Entity(post_id="t", text=text, type=etype, span_start=start, span_end=end)


def test_same_sentence_weight_is_1():
    text = "Путин встретился с Эрдоганом в Кремле."
    entities = [
        _ent("Путин", EntityType.PER, text.index("Путин"), text.index("Путин") + len("Путин")),
        _ent(
            "Эрдоганом",
            EntityType.PER,
            text.index("Эрдоганом"),
            text.index("Эрдоганом") + len("Эрдоганом"),
        ),
        _ent("Кремле", EntityType.LOC, text.index("Кремле"), text.index("Кремле") + len("Кремле")),
    ]
    rels = RelationExtractorService.extract(text, entities, post_id="p1")
    assert len(rels) == 3
    assert all(r.weight == 1.0 for r in rels)


def test_neighbour_sentence_uses_lower_weight():
    text = "Путин встретился с лидерами G20. На саммите присутствовал и премьер‑министр."
    entities = [
        _ent("Путин", EntityType.PER, text.index("Путин"), text.index("Путин") + 5),
        _ent("G20", EntityType.ORG, text.index("G20"), text.index("G20") + 3),
        _ent(
            "премьер‑министр",
            EntityType.PER,
            text.index("премьер‑министр"),
            text.index("премьер‑министр") + len("премьер‑министр"),
        ),
    ]
    rels = RelationExtractorService.extract(text, entities, post_id="p1")
    same = [r for r in rels if r.weight == 1.0]
    neighbour = [r for r in rels if r.weight == WINDOW_WEIGHTS[1]]
    assert len(same) >= 1, "Путин ↔ G20 ожидается same-sentence"
    assert len(neighbour) >= 1, "Путин/G20 ↔ премьер ожидается neighbour"


def test_far_apart_pairs_dropped():
    s1 = "Москва — крупный город."
    s2 = "Сегодня тёплая погода."
    s3 = "Завтра тоже будет жарко."
    s4 = "В обед прошёл дождь."
    s5 = "В Берлине появился премьер."
    text = " ".join([s1, s2, s3, s4, s5])
    entities = [
        _ent("Москва", EntityType.LOC, 0, 6),
        _ent("Берлине", EntityType.LOC, text.index("Берлине"), text.index("Берлине") + 7),
    ]
    rels = RelationExtractorService.extract(text, entities, post_id="p1")
    assert rels == []


def test_no_relations_for_single_entity():
    text = "Москва — столица."
    entities = [_ent("Москва", EntityType.LOC, 0, 6)]
    assert RelationExtractorService.extract(text, entities, post_id="p1") == []


def test_undirected_pairs_not_duplicated():
    text = "Путин и Эрдоган встретились."
    entities = [
        _ent("Путин", EntityType.PER, 0, 5),
        _ent("Эрдоган", EntityType.PER, 8, 15),
    ]
    rels = RelationExtractorService.extract(text, entities, post_id="p1")
    assert len(rels) == 1
