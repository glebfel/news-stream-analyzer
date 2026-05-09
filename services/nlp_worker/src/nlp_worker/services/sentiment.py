from typing import Protocol

from news_common.models import SentimentLabel

POSITIVE_LEX = {
    "рост",
    "успех",
    "победа",
    "прибыль",
    "выигрыш",
    "выиграть",
    "достижение",
    "развитие",
    "увеличение",
    "улучшение",
    "поддержка",
    "запуск",
    "открытие",
    "награда",
    "рекорд",
    "соглашение",
    "сотрудничество",
    "одобрение",
    "хороший",
    "превосходный",
    "позитивный",
}

NEGATIVE_LEX = {
    "падение",
    "кризис",
    "отставка",
    "провал",
    "убыток",
    "потеря",
    "снижение",
    "санкция",
    "штраф",
    "конфликт",
    "арест",
    "обвинение",
    "увольнение",
    "ущерб",
    "атака",
    "утечка",
    "проблема",
    "нарушение",
    "критика",
    "опасность",
    "плохой",
    "негативный",
    "разочарование",
}


class SentimentService(Protocol):
    def predict(self, text: str) -> tuple[SentimentLabel, float]: ...


class LexiconSentimentService:
    def predict(self, text: str) -> tuple[SentimentLabel, float]:
        lower = text.lower()
        pos = sum(1 for w in POSITIVE_LEX if w in lower)
        neg = sum(1 for w in NEGATIVE_LEX if w in lower)
        if pos == neg:
            return SentimentLabel.NEUTRAL, 0.5
        score = (pos - neg) / max(pos + neg, 1)
        if score > 0:
            return SentimentLabel.POSITIVE, min(0.5 + score / 2, 0.99)
        return SentimentLabel.NEGATIVE, min(0.5 + abs(score) / 2, 0.99)


class TransformerSentimentService:
    MODEL_NAME = "blanchefort/rubert-base-cased-sentiment"

    def __init__(self) -> None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self._torch = torch
        self._tokenizer = AutoTokenizer.from_pretrained(self.MODEL_NAME)
        self._model = AutoModelForSequenceClassification.from_pretrained(self.MODEL_NAME)
        self._model.eval()
        self._labels = {
            0: SentimentLabel.NEUTRAL,
            1: SentimentLabel.POSITIVE,
            2: SentimentLabel.NEGATIVE,
        }

    def predict(self, text: str) -> tuple[SentimentLabel, float]:
        with self._torch.no_grad():
            enc = self._tokenizer(text, truncation=True, max_length=512, return_tensors="pt")
            logits = self._model(**enc).logits[0]
            probs = self._torch.softmax(logits, dim=-1)
            idx = int(self._torch.argmax(probs).item())
        return self._labels[idx], float(probs[idx].item())


def build_sentiment_service(mode: str) -> SentimentService:
    if mode == "full":
        return TransformerSentimentService()
    return LexiconSentimentService()
