import networkx as nx
import plotly.graph_objects as go
import streamlit as st

from dashboard.services.api_client import ApiClient

TYPE_COLORS = {
    "PER": "#3b82f6",
    "ORG": "#10b981",
    "LOC": "#ef4444",
    "EVENT": "#f59e0b",
}
TYPE_LABELS = {"PER": "Персона", "ORG": "Организация", "LOC": "Локация", "EVENT": "Событие"}


def render(api: ApiClient) -> None:
    st.html(
        """
        <style>
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
    col_entity, col_limit = st.columns([3, 1])
    with col_entity:
        entity = st.text_input("Сущность", value="Москва", key="graph_entity")
    with col_limit:
        limit = st.slider(
            "Связей", min_value=20, max_value=200, value=60, step=10, key="graph_limit"
        )
    if not entity:
        return
    data = api.subgraph(entity=entity, limit=limit)
    if not data["nodes"]:
        st.info("Связей не найдено — возможно, сущность ещё не появилась в графе.")
        return

    g = nx.Graph()
    for k, n in data["nodes"].items():
        g.add_node(k, **n)
    for e in data["edges"]:
        g.add_edge(e["head"], e["tail"], weight=e["weight"], sentiment=e["sentiment"])

    pos = nx.spring_layout(g, seed=42, k=0.6)
    fig = go.Figure()

    max_weight = max((d["weight"] for _, _, d in g.edges(data=True)), default=1.0)
    for u, v, d in g.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        width = 0.6 + 3.5 * (d["weight"] / max_weight)
        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(width=width, color="rgba(120,120,120,0.4)"),
                hoverinfo="skip",
                showlegend=False,
            )
        )

    nodes_by_type: dict[str, list[str]] = {}
    for n in g.nodes():
        nodes_by_type.setdefault(g.nodes[n].get("type") or "OTHER", []).append(n)

    max_mentions = max(
        (g.nodes[n].get("mention_count", 1) for n in g.nodes()),
        default=1,
    )
    for etype, nodes in nodes_by_type.items():
        x = [pos[n][0] for n in nodes]
        y = [pos[n][1] for n in nodes]
        text = [g.nodes[n].get("text", n) for n in nodes]
        sizes = [12 + 24 * (g.nodes[n].get("mention_count", 1) / max_mentions) for n in nodes]
        hover = [
            f"<b>{g.nodes[n].get('text', n)}</b><br>"
            f"тип: {TYPE_LABELS.get(etype, etype)}<br>"
            f"упоминаний: {g.nodes[n].get('mention_count', 0)}<br>"
            f"wikidata: {g.nodes[n].get('wikidata_id') or '—'}"
            for n in nodes
        ]
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers+text",
                text=text,
                textposition="top center",
                textfont=dict(size=10),
                hovertext=hover,
                hoverinfo="text",
                marker=dict(
                    size=sizes,
                    color=TYPE_COLORS.get(etype, "#6b7280"),
                    line=dict(width=1, color="white"),
                ),
                name=TYPE_LABELS.get(etype, etype),
            )
        )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=650,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"Узлов: {g.number_of_nodes()}, рёбер: {g.number_of_edges()}. "
        "Размер узла — число упоминаний, толщина связи — вес (с учётом decay)."
    )
