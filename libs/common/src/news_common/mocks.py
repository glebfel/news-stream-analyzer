import random
import uuid
from datetime import datetime, timedelta

from news_common.models import RawPost, Source

NEWS_TEMPLATES = [
    "Президент России Владимир Путин провёл встречу с главой {org} в Кремле.",
    "Компания {org} объявила о запуске нового продукта на российском рынке.",
    "В {loc} прошёл международный форум с участием представителей {org}.",
    "Министр финансов {per} прокомментировал ситуацию на валютном рынке.",
    "Сборная России по футболу выиграла товарищеский матч в {loc}.",
    "{org} сообщила о росте выручки на 25% за квартал.",
    "В {loc} началось строительство нового технопарка при поддержке {org}.",
    "Глава {org} {per} объявил об отставке с поста генерального директора.",
    "Студенты {org} победили в международной олимпиаде по программированию.",
    "Курс доллара упал ниже 90 рублей впервые за полгода, отмечают аналитики {org}.",
    "Премьер‑министр посетил завод {org} в {loc} и осмотрел производственные линии.",
    "{per} назначен новым министром цифрового развития, сообщила пресс‑служба.",
    "Учёные {org} опубликовали исследование о влиянии климата на экосистему {loc}.",
    "В {loc} прошла премьера фильма с участием {per}.",
    "Хакерская атака на серверы {org} привела к утечке данных пользователей.",
]

ORGS = [
    "Сбербанк",
    "Яндекс",
    "Газпром",
    "Роснефть",
    "ВТБ",
    "МТС",
    "Лукойл",
    "Тинькофф",
    "Mail.ru Group",
    "ВШЭ",
]
LOCS = ["Москва", "Санкт-Петербург", "Казань", "Новосибирск", "Сочи", "Екатеринбург", "Владивосток"]
PERS = [
    "Сергей Иванов",
    "Анна Петрова",
    "Дмитрий Медведев",
    "Михаил Мишустин",
    "Эльвира Набиуллина",
    "Герман Греф",
]
VK_COMMUNITIES = ["ria", "tassagency", "rbc_news", "lentaru", "meduzaproject"]
TG_CHANNELS = ["ria", "tass_agency", "bbcrussian", "rbc_news", "mash"]


def fake_post(source: Source, channel: str | None = None) -> RawPost:
    template = random.choice(NEWS_TEMPLATES)
    text = template.format(
        org=random.choice(ORGS),
        loc=random.choice(LOCS),
        per=random.choice(PERS),
    )
    posted = datetime.utcnow() - timedelta(minutes=random.randint(0, 1440))
    pid = f"{source.value}_{uuid.uuid4().hex[:12]}"
    return RawPost(
        id=pid,
        source=source,
        author=random.choice(PERS) if source == Source.VK else None,
        channel=channel
        or (random.choice(VK_COMMUNITIES) if source == Source.VK else random.choice(TG_CHANNELS)),
        text=text,
        url=f"https://example.com/{pid}",
        posted_at=posted,
        likes=random.randint(0, 5000),
        reposts=random.randint(0, 1000),
        views=random.randint(100, 100000),
    )


def fake_batch(source: Source, n: int) -> list[RawPost]:
    return [fake_post(source) for _ in range(n)]
