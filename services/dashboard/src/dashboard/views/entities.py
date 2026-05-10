import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.services.api_client import ApiClient

TYPE_LABELS: dict[str | None, str] = {
    None: "Все типы",
    "PER": "Персоны",
    "ORG": "Организации",
    "LOC": "Локации",
}


def render(api: ApiClient) -> None:
    col_type, col_size = st.columns([1, 1])
    with col_type:
        etype = st.selectbox(
            "Тип сущности",
            options=[None, "PER", "ORG", "LOC"],
            format_func=lambda v: TYPE_LABELS[v],
        )
    with col_size:
        size = st.slider("Сколько показывать", min_value=10, max_value=100, value=30, step=5)
    data = api.top_entities(etype=etype, size=size)
    df = pd.DataFrame(data["items"])
    if df.empty:
        st.info("Сущностей пока нет.")
        return
    df = df.rename(columns={"key": "Сущность", "doc_count": "Упоминаний"})
    st.plotly_chart(
        px.bar(df, x="Сущность", y="Упоминаний", title="Топ сущностей").update_layout(
            xaxis_tickangle=-45
        ),
        use_container_width=True,
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
