import plotly.graph_objects as go
import streamlit as st

from dashboard.services.api_client import ApiClient

TYPE_LABELS: dict[str | None, str] = {
    None: "Все типы",
    "PER": "Персоны",
    "ORG": "Организации",
    "LOC": "Локации",
}
CHANNEL_COLOR = "rgba(59,130,246,0.55)"
ENTITY_COLOR = "rgba(16,185,129,0.55)"


def render(api: ApiClient) -> None:
    # SVG `fill` is a presentation attribute, but Plotly writes it inline; CSS
    # with !important overrides it. `currentColor` inherits the parent text
    # color, which Streamlit recolors on light/dark switch without a rerun.
    st.html(
        """
        <style>
        .js-plotly-plot .sankey text,
        .js-plotly-plot .sankey-node text,
        .js-plotly-plot text {
            fill: currentColor !important;
            stroke: none !important;
            stroke-width: 0 !important;
            paint-order: fill !important;
            text-shadow: none !important;
            filter: none !important;
        }
        </style>
        """
    )
    st.caption(
        "Связь источников и сущностей: ширина потока — количество упоминаний. "
        "Видно, кто и о чём пишет чаще всего."
    )
    col_t, col_n, col_p = st.columns(3, gap="small", vertical_alignment="bottom")
    with col_t:
        etype = st.selectbox(
            "Тип сущности",
            options=[None, "PER", "ORG", "LOC"],
            format_func=lambda v: TYPE_LABELS[v],
            key="sankey_etype",
        )
    with col_n:
        channels = st.slider(
            "Источников", min_value=3, max_value=15, value=8, key="sankey_channels"
        )
    with col_p:
        per_channel = st.slider(
            "Сущностей на источник",
            min_value=3,
            max_value=10,
            value=5,
            key="sankey_per_channel",
        )

    rows = api.sankey(channels=channels, per_channel=per_channel, etype=etype)
    if not rows:
        st.info("Пока нет данных — подожди, пока отработает свежий пайплайн.")
        return

    channels_idx: dict[str, int] = {}
    entities_idx: dict[str, int] = {}
    for r in rows:
        ch = str(r["channel"])
        ent = str(r["entity"])
        if ch not in channels_idx:
            channels_idx[ch] = len(channels_idx)
        if ent not in entities_idx:
            entities_idx[ent] = len(entities_idx)
    n_channels = len(channels_idx)
    labels = list(channels_idx) + list(entities_idx)
    colors = [CHANNEL_COLOR] * n_channels + [ENTITY_COLOR] * len(entities_idx)

    sources = [channels_idx[str(r["channel"])] for r in rows]
    targets = [n_channels + entities_idx[str(r["entity"])] for r in rows]
    values = [int(r["count"]) for r in rows]

    max_label_chars = 22
    short_labels = [
        lbl if len(lbl) <= max_label_chars else lbl[: max_label_chars - 1] + "…" for lbl in labels
    ]
    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                label=short_labels,
                customdata=labels,
                color=colors,
                pad=22,
                thickness=22,
                line=dict(width=0),
                hovertemplate="%{customdata}<extra></extra>",
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color="rgba(120,120,120,0.3)",
                hovertemplate="%{source.customdata} → %{target.customdata}<br>"
                "упоминаний: %{value}<extra></extra>",
            ),
            textfont=dict(size=14, family="Arial, sans-serif"),
        )
    )
    height = max(550, 32 * max(n_channels, len(entities_idx)))
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=10, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Источников: {n_channels}, сущностей: {len(entities_idx)}, связей: {len(rows)}")
