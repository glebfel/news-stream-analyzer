from news_common.models import SentimentLabel
from nlp_worker.services.sentiment import LexiconSentimentService


def test_lexicon_positive():
    s = LexiconSentimentService()
    label, score = s.predict("Компания показала рост и достигла рекордной прибыли")
    assert label == SentimentLabel.POSITIVE
    assert score > 0.5


def test_lexicon_negative():
    s = LexiconSentimentService()
    label, _ = s.predict("Падение акций, кризис и серьёзный убыток для компании")
    assert label == SentimentLabel.NEGATIVE


def test_lexicon_neutral():
    s = LexiconSentimentService()
    label, _ = s.predict("Сегодня прошла встреча в офисе")
    assert label == SentimentLabel.NEUTRAL
