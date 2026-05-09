import streamlit as st
from news_common import get_settings

from dashboard.services.api_client import ApiClient
from dashboard.views import entities, graph, search, stats

settings = get_settings()

st.set_page_config(page_title="News Stream Analyzer", layout="wide")
st.title("Система потокового анализа новостей")

api = ApiClient(settings.api_base_url)
tab_search, tab_stats, tab_entities, tab_graph = st.tabs(
    ["Поиск", "Статистика", "Сущности", "Граф"]
)

with tab_search:
    search.render(api)

with tab_stats:
    stats.render(api)

with tab_entities:
    entities.render(api)

with tab_graph:
    graph.render(api)
