import folium
import streamlit as st
from streamlit_folium import st_folium

from dashboard.services.api_client import ApiClient


def render(api: ApiClient) -> None:
    st.caption(
        "Локации из новостного потока на карте мира. "
        "Координаты подтянуты из Wikidata по найденным QID; "
        "размер маркера пропорционален числу упоминаний."
    )
    size = st.slider(
        "Сколько локаций",
        min_value=10,
        max_value=100,
        value=30,
        step=5,
        key="map_size",
    )
    with st.spinner("Запрашиваю Wikidata за координатами…"):
        rows = api.locations(size=size)
    if not rows:
        st.info("Пока нет локаций с привязкой к Wikidata. Подождите свежих постов.")
        return

    fmap = folium.Map(location=[55, 50], zoom_start=2, tiles="cartodbpositron")
    max_count = max(r["mention_count"] for r in rows)
    for r in rows:
        radius = 4 + 16 * (r["mention_count"] / max_count)
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=radius,
            color="#ef4444",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.7,
            weight=1,
            popup=folium.Popup(
                f"<b>{r['text']}</b><br>"
                f"упоминаний: {r['mention_count']}<br>"
                f"<a href='https://www.wikidata.org/wiki/{r['wikidata_id']}' "
                f"target='_blank'>{r['wikidata_id']}</a>",
                max_width=240,
            ),
        ).add_to(fmap)
    st_folium(fmap, width=None, height=600, returned_objects=[])
    st.caption(f"Точек на карте: {len(rows)}")
