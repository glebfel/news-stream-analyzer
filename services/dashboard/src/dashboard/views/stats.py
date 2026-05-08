import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.services.api_client import ApiClient


def render(api: ApiClient) -> None:
    data = api.stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Всего постов", data["posts_total"])
        df_src = pd.DataFrame(data["by_source"])
        if not df_src.empty:
            st.plotly_chart(
                px.bar(df_src, x="key", y="doc_count", title="По источникам"),
                use_container_width=True,
            )
    with col2:
        df_sent = pd.DataFrame(data["by_sentiment"])
        if not df_sent.empty:
            st.plotly_chart(
                px.pie(df_sent, names="key", values="doc_count", title="Тональность"),
                use_container_width=True,
            )
    df_day = pd.DataFrame(data["by_day"])
    if not df_day.empty:
        df_day["key_as_string"] = pd.to_datetime(df_day["key_as_string"])
        st.plotly_chart(
            px.line(df_day, x="key_as_string", y="doc_count", title="Динамика по дням"),
            use_container_width=True,
        )
