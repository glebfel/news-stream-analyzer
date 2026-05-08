from processor.services.normalizer import Normalizer


def test_clean_strips_urls_and_emoji():
    n = Normalizer()
    src = "Привет 👋 https://example.com и @user #tag — это тест!"
    out = n.clean(src)
    assert "https://" not in out
    assert "👋" not in out
    assert "@user" not in out
    assert "тест" in out


def test_tokenize_returns_lemmas():
    n = Normalizer()
    tokens, lemmas = n.tokenize("Москвичи открыли новые магазины")
    assert "москвич" in lemmas
    assert "открыть" in lemmas
    assert len(tokens) == len(lemmas)
