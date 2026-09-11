import os
import html

import networkx as nx
from pyvis.network import Network


GRAPH_FILE = "output/criminal_network.graphml"
DEFAULT_OUTPUT = "output/investigation_network.html"


def find_entity(graph, entity_name):
    """
    Find an entity in the graph using case-insensitive matching.
    """

    search_name = str(entity_name).strip().casefold()

    for node in graph.nodes:

        if str(node).strip().casefold() == search_name:

            return node

    return None


def get_entity_type(graph, node):
    """
    Return the entity type stored in the normalized graph.
    """

    node_data = graph.nodes[node]

    entity_type = node_data.get(
        "entity_type",
        "ENTITY"
    )

    if not entity_type:
        entity_type = "ENTITY"

    return str(entity_type)


def get_entity_color(entity_type):
    """
    Assign a consistent visual category to each entity type.
    """

    colors = {
        "PERSON": "#4FC3F7",
        "COMPLAINANT": "#42A5F5",
        "ACCUSED": "#EF5350",
        "STATE": "#AB47BC",
        "DISTRICT": "#7E57C2",
        "POLICE_STATION": "#26A69A",
        "CRIME_CATEGORY": "#FFA726",
        "LEGAL_SECTION": "#EC407A",
        "VEHICLE": "#66BB6A",
        "ORGANIZATION": "#29B6F6",
        "PHONE": "#8D6E63",
        "BANK_ACCOUNT": "#5C6BC0",
        "LOCATION": "#26C6DA",
        "ENTITY": "#90A4AE"
    }

    return colors.get(
        entity_type.upper(),
        colors["ENTITY"]
    )


def build_entity_network(
    entity_name,
    output_file=DEFAULT_OUTPUT,
    depth=1,
    max_neighbors=100
):
    """
    Build a focused investigation network for any entity.

    Parameters
    ----------
    entity_name : str
        Entity to investigate.

    output_file : str
        HTML output path.

    depth : int
        Network depth around the selected entity.
        1 = direct connections.
        2 = second-degree connections.

    max_neighbors : int
        Maximum number of direct neighbors displayed.
    """

    if not os.path.exists(GRAPH_FILE):

        raise FileNotFoundError(
            f"Normalized graph not found: {GRAPH_FILE}"
        )

    print("\n==========================================")
    print(" ENTITY INVESTIGATION NETWORK")
    print("==========================================\n")

    print("Loading normalized investigation graph...")

    graph = nx.read_graphml(
        GRAPH_FILE
    )

    print(
        "Total graph nodes:",
        graph.number_of_nodes()
    )

    print(
        "Total graph relationships:",
        graph.number_of_edges()
    )

    # ------------------------------------------
    # FIND ENTITY
    # ------------------------------------------

    selected_node = find_entity(
        graph,
        entity_name
    )

    if selected_node is None:

        raise ValueError(
            f"Entity not found: {entity_name}"
        )

    print(
        "Selected entity:",
        selected_node
    )

    selected_type = get_entity_type(
        graph,
        selected_node
    )

    print(
        "Entity type:",
        selected_type
    )

    # ------------------------------------------
    # BUILD FOCUSED SUBGRAPH
    # ------------------------------------------

    if depth < 1:
        depth = 1

    if depth > 2:
        depth = 2

    focused_nodes = set()

    focused_nodes.add(
        selected_node
    )

    current_nodes = {
        selected_node
    }

    for _ in range(depth):

        next_nodes = set()

        for node in current_nodes:

            # Do not expand extremely high-degree hub entities.
            # They can connect thousands of unrelated records and
            # make a focused investigation network unreadable.
            if graph.degree(node) > max_neighbors:
                continue

            neighbors = list(
                graph.neighbors(node)
            )

            # Prevent extremely large visualizations.
            if len(neighbors) > max_neighbors:

                neighbors = sorted(
                    neighbors,
                    key=lambda n: graph.degree(n),
                    reverse=True
                )[:max_neighbors]

            next_nodes.update(
                neighbors
            )

        focused_nodes.update(
            next_nodes
        )

        current_nodes = next_nodes

    focused_graph = graph.subgraph(
        focused_nodes
    ).copy()

    print(
        "Focused network nodes:",
        focused_graph.number_of_nodes()
    )

    print(
        "Focused network relationships:",
        focused_graph.number_of_edges()
    )

    # ------------------------------------------
    # CREATE PYVIS NETWORK
    # ------------------------------------------

    net = Network(
        height="700px",
        width="100%",
        bgcolor="#0b0f14",
        font_color="#f5f5f5",
        directed=False
    )

    net.set_options(
        """
        {
          "interaction": {
            "hover": true,
            "navigationButtons": true,
            "keyboard": true,
            "multiselect": false
          },

          "physics": {
            "enabled": true,
            "solver": "forceAtlas2Based",

            "forceAtlas2Based": {
              "gravitationalConstant": -55,
              "centralGravity": 0.02,
              "springLength": 130,
              "springConstant": 0.08,
              "damping": 0.7,
              "avoidOverlap": 1
            },

            "minVelocity": 0.75,
            "stabilization": {
              "enabled": true,
              "iterations": 500
            }
          },

          "nodes": {
            "borderWidth": 2,
            "shadow": true,

            "font": {
              "face": "Inter",
              "size": 15,
              "color": "#ffffff"
            }
          },

          "edges": {
            "smooth": {
              "enabled": true,
              "type": "dynamic"
            },

            "color": {
              "inherit": false,
              "opacity": 0.65
            },

            "font": {
              "size": 10,
              "color": "#cfd8dc",
              "strokeWidth": 0
            }
          }
        }
        """
    )

    # ------------------------------------------
    # ADD NODES
    # ------------------------------------------

    for node, data in focused_graph.nodes(
        data=True
    ):

        node_name = str(node)

        entity_type = get_entity_type(
            focused_graph,
            node
        )

        degree = focused_graph.degree(
            node
        )

        is_selected = (
            node == selected_node
        )

        # Selected investigation target
        if is_selected:

            shape = "star"
            size = 34

        else:

            shape = "dot"
            size = min(
                25,
                max(
                    12,
                    10 + degree * 1.5
                )
            )

        label = node_name

        # Keep labels readable.
        if not is_selected and degree < 2:

            label = ""

        title = (
            "<div style='font-family:Arial'>"
            f"<b>Entity:</b> "
            f"{html.escape(node_name)}"
            "<br>"
            f"<b>Type:</b> "
            f"{html.escape(entity_type)}"
            "<br>"
            f"<b>Connections in view:</b> "
            f"{degree}"
            "</div>"
        )

        net.add_node(
            node,
            label=label,
            title=title,
            shape=shape,
            size=size,
            color=get_entity_color(
                entity_type
            )
        )

    # ------------------------------------------
    # ADD RELATIONSHIPS
    # ------------------------------------------

    for source, target, data in focused_graph.edges(
        data=True
    ):

        relationship = data.get(
            "relationship",
            "CONNECTED_TO"
        )

        net.add_edge(
            source,
            target,
            title=str(
                relationship
            ),
            label=str(
                relationship
            )
        )

    # ------------------------------------------
    # SAVE
    # ------------------------------------------

    os.makedirs(
        os.path.dirname(output_file),
        exist_ok=True
    )

    net.write_html(
        output_file,
        notebook=False
    )

    print("\n==========================================")
    print(" INVESTIGATION NETWORK COMPLETE")
    print("==========================================\n")

    print(
        "Entity:",
        selected_node
    )

    print(
        "Entity type:",
        selected_type
    )

    print(
        "Network depth:",
        depth
    )

    print(
        "Nodes displayed:",
        focused_graph.number_of_nodes()
    )

    print(
        "Relationships displayed:",
        focused_graph.number_of_edges()
    )

    print(
        "Output:",
        output_file
    )

    return output_file


if __name__ == "__main__":

    test_entity = "Ganga Dyal"

    build_entity_network(
        test_entity,
        depth=1
    )