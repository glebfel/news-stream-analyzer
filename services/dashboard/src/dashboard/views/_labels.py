from zoneinfo import ZoneInfo

from news_common import get_settings

DISPLAY_TZ = ZoneInfo(get_settings().display_timezone)

SOURCE_LABELS_FULL: dict[str | None, str] = {
    None: "Все источники",
    "vk": "ВКонтакте",
    "telegram": "Telegram",
}
SOURCE_LABELS: dict[str, str] = {"vk": "ВКонтакте", "telegram": "Telegram"}

TYPE_LABELS_FILTER: dict[str | None, str] = {
    None: "Все типы",
    "PER": "Персоны",
    "ORG": "Организации",
    "LOC": "Локации",
}
TYPE_LABELS_NODE = {
    "PER": "Персона",
    "ORG": "Организация",
    "LOC": "Локация",
    "EVENT": "Событие",
}
TYPE_COLORS = {
    "PER": "#3b82f6",
    "ORG": "#10b981",
    "LOC": "#ef4444",
    "EVENT": "#f59e0b",
}

SENTIMENT_LABELS = {"positive": "позитив", "negative": "негатив", "neutral": "нейтрально"}
SENTIMENT_COLORS = {"позитив": "#10b981", "негатив": "#ef4444", "нейтрально": "#94a3b8"}
