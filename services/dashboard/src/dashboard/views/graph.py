import networkx as nx
import plotly.graph_objects as go
import streamlit as st

from dashboard.services.api_client import ApiClient


def render(api: ApiClient) -> None:
    entity = st.text_input("Сущность", value="Москва")
    if not entity:
        return
    data = api.subgraph(entity=entity, limit=80)
    if not data["nodes"]:
        st.info("Связей не найдено — возможно, сущность ещё не появилась в графе.")
        return

    g = nx.Graph()
    for k, n in data["nodes"].items():
        g.add_node(k, **n)
    for e in data["edges"]:
        g.add_edge(e["head"], e["tail"], weight=e["weight"], sentiment=e["sentiment"])

    pos = nx.spring_layout(g, seed=42)
    edge_x, edge_y = [], []
    for u, v in g.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    node_x = [pos[n][0] for n in g.nodes()]
    node_y = [pos[n][1] for n in g.nodes()]
    labels = [g.nodes[n].get("text", n) for n in g.nodes()]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x, y=edge_y, mode="lines", line=dict(width=0.5, color="#888"), hoverinfo="none"
        )
    )
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=labels,
            textposition="top center",
            marker=dict(size=14, color="#1f77b4"),
        )
    )
    fig.update_layout(showlegend=False, height=600, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
