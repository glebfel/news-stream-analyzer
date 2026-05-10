from datetime import datetime
from typing import Any

import streamlit as st
from streamlit_searchbox import st_searchbox

from dashboard.services.api_client import ApiClient

SOURCE_LABELS: dict[str | None, str] = {
    None: "Все источники",
    "vk": "ВКонтакте",
    "telegram": "Telegram",
}


def render(api: ApiClient) -> None:
    col_q, col_src = st.columns([3, 1])
    with col_q:
        q = st_searchbox(
            search_function=lambda term: api.suggest(term, size=10) if term else [],
            placeholder="Начните вводить — появятся подсказки по сущностям",
            label="Поисковый запрос",
            default="Москва",
            key="search_query",
        )
    with col_src:
        src = st.selectbox(
            "Источник",
            options=[None, "vk", "telegram"],
            format_func=lambda v: SOURCE_LABELS[v],
        )
    if not q:
        return
    data = api.search(q=q, size=20, source=src)
    st.caption(f"Найдено: {data['total']}")
    for item in data["items"]:
        with st.container(border=True):
            st.markdown(_header(item))
            st.write(item.get("text_clean") or item.get("text"))


def _header(item: dict[str, Any]) -> str:
    source = item.get("source")
    label = SOURCE_LABELS.get(source, source or "?")
    channel = (item.get("metadata") or {}).get("channel")
    ts = _format_ts(item.get("posted_at"))
    parts = [f"**{label}**"]
    if channel:
        parts.append(f"`{channel}`")
    if ts:
        parts.append(ts)
    url = (item.get("metadata") or {}).get("url")
    if url:
        parts.append(f"[открыть оригинал ↗]({url})")
    return " · ".join(parts)


def _format_ts(ts: str | None) -> str:
    if not ts:
        return ""
    try:
        return datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return ts
