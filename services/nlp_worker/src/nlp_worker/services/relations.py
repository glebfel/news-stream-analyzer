from news_common.models import Entity, Relation
from razdel import sentenize

# Sentence-distance weights: closer pairs contribute more to the edge weight.
WINDOW_WEIGHTS = {0: 1.0, 1: 0.7, 2: 0.5, 3: 0.3}
WINDOW_RADIUS = max(WINDOW_WEIGHTS)


class RelationExtractorService:
    @staticmethod
    def extract(text: str, entities: list[Entity], post_id: str) -> list[Relation]:
        if len(entities) < 2:
            return []

        sentences = list(sentenize(text))
        if not sentences:
            return []

        per_sentence: list[list[Entity]] = [[] for _ in sentences]
        for ent in entities:
            for i, sent in enumerate(sentences):
                if ent.span_start >= sent.start and ent.span_end <= sent.stop:
                    per_sentence[i].append(ent)
                    break

        rels: list[Relation] = []
        seen: set[tuple[str, str, str, str, int]] = set()

        for i, head_bucket in enumerate(per_sentence):
            if not head_bucket:
                continue
            for j in range(i, min(i + WINDOW_RADIUS + 1, len(sentences))):
                tail_bucket = per_sentence[j]
                if not tail_bucket:
                    continue
                weight = WINDOW_WEIGHTS[j - i]
                for k, head in enumerate(head_bucket):
                    starts = (k + 1) if i == j else 0
                    for tail in tail_bucket[starts:]:
                        if head.text == tail.text and head.type == tail.type:
                            continue
                        key = (
                            min(head.text, tail.text),
                            min(head.type, tail.type),
                            max(head.text, tail.text),
                            max(head.type, tail.type),
                            j - i,
                        )
                        if key in seen:
                            continue
                        seen.add(key)
                        rels.append(
                            Relation(
                                post_id=post_id,
                                head=head.text,
                                head_type=head.type,
                                tail=tail.text,
                                tail_type=tail.type,
                                rel_type="co_occurrence",
                                weight=weight,
                                sentence=sentences[i].text
                                if i == j
                                else f"{sentences[i].text} ⇢ {sentences[j].text}",
                            )
                        )
        return rels
