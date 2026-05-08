import re

import pymorphy3
from razdel import tokenize


class Normalizer:
    _URL = re.compile(r"https?://\S+|www\.\S+")
    _MENTION = re.compile(r"[@#][\w_]+")
    _EMOJI = re.compile(
        "["
        "\U0001f1e0-\U0001f1ff"
        "\U0001f300-\U0001f5ff"
        "\U0001f600-\U0001f64f"
        "\U0001f680-\U0001f6ff"
        "\U0001f700-\U0001f77f"
        "\U0001f900-\U0001f9ff"
        "☀-⛿"
        "✀-➿"
        "]+",
        flags=re.UNICODE,
    )
    _WS = re.compile(r"\s+")

    def __init__(self) -> None:
        self._morph = pymorphy3.MorphAnalyzer()

    def clean(self, text: str) -> str:
        text = self._URL.sub(" ", text)
        text = self._MENTION.sub(" ", text)
        text = self._EMOJI.sub(" ", text)
        text = self._WS.sub(" ", text)
        return text.strip()

    def tokenize(self, text: str) -> tuple[list[str], list[str]]:
        tokens = [t.text for t in tokenize(text) if t.text.strip()]
        lemmas = [self._morph.parse(t)[0].normal_form for t in tokens]
        return tokens, lemmas
