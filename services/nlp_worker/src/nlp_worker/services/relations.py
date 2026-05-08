from news_common.models import Entity, Relation
from razdel import sentenize


class RelationExtractorService:
    @staticmethod
    def extract(text: str, entities: list[Entity], post_id: str) -> list[Relation]:
        if len(entities) < 2:
            return []

        sentences = list(sentenize(text))
        rels: list[Relation] = []
        for sent in sentences:
            in_sent = [
                e for e in entities if e.span_start >= sent.start and e.span_end <= sent.stop
            ]
            for i, head in enumerate(in_sent):
                for tail in in_sent[i + 1 :]:
                    if head.text == tail.text:
                        continue
                    rels.append(
                        Relation(
                            post_id=post_id,
                            head=head.text,
                            head_type=head.type,
                            tail=tail.text,
                            tail_type=tail.type,
                            rel_type="co_occurrence",
                            weight=1.0,
                            sentence=sent.text,
                        )
                    )
        return rels
