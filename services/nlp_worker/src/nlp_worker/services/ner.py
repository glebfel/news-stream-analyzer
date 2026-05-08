from natasha import (
    Doc,
    MorphVocab,
    NamesExtractor,
    NewsEmbedding,
    NewsMorphTagger,
    NewsNERTagger,
    NewsSyntaxParser,
    Segmenter,
)
from news_common.models import Entity, EntityType

_NATASHA_TYPE: dict[str, EntityType] = {
    "PER": EntityType.PER,
    "ORG": EntityType.ORG,
    "LOC": EntityType.LOC,
}


class NerService:
    def __init__(self) -> None:
        self._segmenter = Segmenter()
        self._morph_vocab = MorphVocab()
        emb = NewsEmbedding()
        self._morph_tagger = NewsMorphTagger(emb)
        self._syntax_parser = NewsSyntaxParser(emb)
        self._ner_tagger = NewsNERTagger(emb)
        self._names_extractor = NamesExtractor(self._morph_vocab)

    def extract(self, text: str, post_id: str) -> list[Entity]:
        doc = Doc(text)
        doc.segment(self._segmenter)
        doc.tag_morph(self._morph_tagger)
        doc.parse_syntax(self._syntax_parser)
        doc.tag_ner(self._ner_tagger)
        for span in doc.spans:
            span.normalize(self._morph_vocab)

        entities: list[Entity] = []
        for span in doc.spans:
            etype = _NATASHA_TYPE.get(span.type)
            if etype is None:
                continue
            entities.append(
                Entity(
                    post_id=post_id,
                    text=span.normal or span.text,
                    type=etype,
                    span_start=span.start,
                    span_end=span.stop,
                    confidence=1.0,
                )
            )
        return entities
