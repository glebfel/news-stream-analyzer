import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.services.api_client import ApiClient


def render(api: ApiClient) -> None:
    etype = st.selectbox("Тип", ["", "PER", "ORG", "LOC", "EVENT"])
    data = api.top_entities(etype=etype or None, size=30)
    df = pd.DataFrame(data["items"])
    if df.empty:
        st.info("Сущностей пока нет.")
        return
    st.plotly_chart(
        px.bar(df, x="key", y="doc_count", title="Топ сущностей").update_layout(
            xaxis_tickangle=-45
        ),
        use_container_width=True,
    )
    st.dataframe(df, use_container_width=True)
