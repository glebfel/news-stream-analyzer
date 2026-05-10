import streamlit as st
from news_common import get_settings

from dashboard.services.api_client import ApiClient
from dashboard.views import entities, graph, live, sankey, search, stats
from dashboard.views import map as map_view

settings = get_settings()

st.set_page_config(page_title="News Stream Analyzer", layout="wide")
st.title("Система потокового анализа новостей")

api = ApiClient(settings.api_base_url)
tab_live, tab_search, tab_stats, tab_entities, tab_graph, tab_sankey, tab_map = st.tabs(
    ["Лента", "Поиск", "Статистика", "Сущности", "Граф", "Источники", "Карта"]
)

with tab_live:
    live.render(api)

with tab_search:
    search.render(api)

with tab_stats:
    stats.render(api)

with tab_entities:
    entities.render(api)

with tab_graph:
    graph.render(api)

with tab_sankey:
    sankey.render(api)

with tab_map:
    map_view.render(api)
