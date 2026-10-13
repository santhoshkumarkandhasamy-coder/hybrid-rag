from pyvis.network import Network


def create_graph_html(graph_data: dict) -> str:
    """Build an interactive PyVis network from entities/relationships."""

    network = Network(
        height="600px",
        width="100%",
        bgcolor="#ffffff",
        font_color="#000000",
        directed=True,
    )

    network.set_options(
        """
        {
          "nodes": {"shape": "dot", "size": 20,
                    "font": {"size": 14}},
          "edges": {"arrows": {"to": {"enabled": true}},
                    "font": {"size": 10, "align": "middle"},
                    "smooth": {"enabled": true}},
          "physics": {"enabled": true,
                      "stabilization": {"iterations": 200}}
        }
        """
    )

    for entity in graph_data.get("entities", []):
        name = entity.get("name", "Unknown")
        network.add_node(
            name,
            label=name,
            title=f"Type: {entity.get('type', 'Entity')}",
        )

    for rel in graph_data.get("relationships", []):
        source, target = rel.get("source"), rel.get("target")
        label = rel.get("relationship") or rel.get("type", "RELATES_TO")

        if source and target:
            network.add_edge(source, target, label=label, title=label)

    return network.generate_html()
