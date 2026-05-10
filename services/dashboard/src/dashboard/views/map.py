import folium
import streamlit as st
from streamlit_folium import st_folium

from dashboard.services.api_client import ApiClient


def render(api: ApiClient) -> None:
    st.caption(
        "Все упомянутые локации из новостного потока на карте мира. "
        "Координаты подтянуты из Wikidata по найденным QID; "
        "размер маркера пропорционален числу упоминаний."
    )
    with st.spinner("Запрашиваю Wikidata за координатами…"):
        rows = api.locations(size=500)
    if not rows:
        st.info("Пока нет локаций с привязкой к Wikidata. Подождите свежих постов.")
        return

    # CARTO Voyager has English-only labels; the default Positron pulls
    # localised glyphs (Chinese/Arabic) which look like noise on a Russian UI.
    fmap = folium.Map(
        location=[55, 50],
        zoom_start=2,
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png",
        attr=(
            '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
            '&copy; <a href="https://carto.com/attributions">CARTO</a>'
        ),
    )
    fmap.get_root().header.add_child(
        folium.Element("<style>.leaflet-attribution-flag{display:none!important;}</style>")
    )
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
