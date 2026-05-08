import streamlit as st

from dashboard.services.api_client import ApiClient


def render(api: ApiClient) -> None:
    q = st.text_input("Поисковый запрос", value="Москва")
    src = st.selectbox("Источник", options=["", "vk", "telegram"])
    if not q:
        return
    data = api.search(q=q, size=20, source=src or None)
    st.caption(f"Найдено: {data['total']}")
    for item in data["items"]:
        with st.container(border=True):
            st.markdown(f"**{item.get('source', '?')}** · {item.get('posted_at', '')}")
            st.write(item.get("text_clean") or item.get("text"))
