import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.services.api_client import ApiClient

SOURCE_LABELS = {"vk": "ВКонтакте", "telegram": "Telegram"}
SENTIMENT_LABELS = {"positive": "позитив", "negative": "негатив", "neutral": "нейтрально"}
SENTIMENT_COLORS = {"позитив": "#10b981", "негатив": "#ef4444", "нейтрально": "#94a3b8"}


def render(api: ApiClient) -> None:
    data = api.stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Всего постов", data["posts_total"])
        df_src = pd.DataFrame(data["by_source"])
        if not df_src.empty:
            df_src["Источник"] = df_src["key"].map(lambda k: SOURCE_LABELS.get(k, k))
            df_src = df_src.rename(columns={"doc_count": "Постов"})
            st.plotly_chart(
                px.bar(df_src, x="Источник", y="Постов", title="По источникам"),
                use_container_width=True,
            )
    with col2:
        df_sent = pd.DataFrame(data["by_sentiment"])
        if not df_sent.empty:
            df_sent["Тональность"] = df_sent["key"].map(lambda k: SENTIMENT_LABELS.get(k, k))
            df_sent = df_sent.rename(columns={"doc_count": "Постов"})
            st.plotly_chart(
                px.pie(
                    df_sent,
                    names="Тональность",
                    values="Постов",
                    title="Тональность",
                    color="Тональность",
                    color_discrete_map=SENTIMENT_COLORS,
                ),
                use_container_width=True,
            )
    df_day = pd.DataFrame(data["by_day"])
    if not df_day.empty:
        df_day["День"] = pd.to_datetime(df_day["key_as_string"])
        df_day = df_day.rename(columns={"doc_count": "Постов"})
        df_day = df_day[df_day["Постов"] > 0].sort_values("День")
        if not df_day.empty:
            cutoff = df_day["День"].max() - pd.Timedelta(days=30)
            df_day = df_day[df_day["День"] >= cutoff]
            st.plotly_chart(
                px.line(
                    df_day,
                    x="День",
                    y="Постов",
                    markers=True,
                    title="Динамика по дням (последние 30 дней)",
                ),
                use_container_width=True,
            )
