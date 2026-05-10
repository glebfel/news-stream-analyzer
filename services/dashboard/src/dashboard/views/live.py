from datetime import datetime
from typing import Any

import streamlit as st

from dashboard.services.api_client import ApiClient

SOURCE_LABELS = {"vk": "ВКонтакте", "telegram": "Telegram"}


def render(api: ApiClient) -> None:
    st.caption("Лента обновляется каждые 10 секунд — посты идут прямо из пайплайна.")
    _stream(api)


@st.fragment(run_every=10)
def _stream(api: ApiClient) -> None:
    data = api.latest(size=10)
    st.caption(f"Последнее обновление: {datetime.now().strftime('%H:%M:%S')}")
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
