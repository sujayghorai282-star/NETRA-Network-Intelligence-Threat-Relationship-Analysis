import os
import html
import json

import networkx as nx
import pandas as pd
from pyvis.network import Network


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_GRAPH = "output/criminal_network.graphml"
RELATIONSHIP_FILE = "output/extracted_relationships.csv"
OUTPUT_FILE = "output/criminal_network.html"

# Browser view only.
# The original GraphML remains untouched.
MAX_NODES = 300


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(INPUT_GRAPH):
    print("ERROR: Criminal network graph not found.")
    print("Expected:", INPUT_GRAPH)
    raise SystemExit(1)


# ============================================================
# LOAD GRAPH
# ============================================================

print("\n======================================")
print(" CRIMINAL NETWORK VISUALIZATION")
print("======================================")

G = nx.read_graphml(INPUT_GRAPH)

print("Original nodes:", G.number_of_nodes())
print("Original relationships:", G.number_of_edges())


# ============================================================
# LOAD RELATIONSHIP INFORMATION
# ============================================================

relationship_types = {}

if os.path.exists(RELATIONSHIP_FILE):

    try:

        relationships_df = pd.read_csv(
            RELATIONSHIP_FILE
        )

        for _, row in relationships_df.iterrows():

            source = str(
                row.get("source", "")
            ).strip()

            target = str(
                row.get("target", "")
            ).strip()

            relationship = str(
                row.get(
                    "relationship",
                    "CONNECTED_TO"
                )
            ).strip()

            if source:
                relationship_types.setdefault(
                    source,
                    set()
                ).add(relationship)

            if target:
                relationship_types.setdefault(
                    target,
                    set()
                ).add(relationship)

        print(
            "Relationship records loaded:",
            len(relationships_df)
        )

    except Exception as e:

        print(
            "WARNING: Relationship metadata unavailable:",
            e
        )


# ============================================================
# ENTITY TYPE DETECTION
# ============================================================

STATES = {
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Delhi"
}


CRIME_KEYWORDS = [
    "crime",
    "offense",
    "offenses",
    "fraud",
    "theft",
    "robbery",
    "murder",
    "assault",
    "harassment",
    "burglary",
    "kidnapping",
    "cybercrime",
    "traffic",
    "violent",
    "sexual"
]


def detect_entity_type(name):

    name = str(name).strip()

    relationships = relationship_types.get(
        name,
        set()
    )

    # State
    if name in STATES:
        return "STATE"

    # Legal section
    name_lower = name.lower()

    if (
        name_lower.startswith("section")
        or "ipc" in name_lower
        or "crpc" in name_lower
        or "bns" in name_lower
    ):
        return "LEGAL SECTION"

    # Crime category
    for keyword in CRIME_KEYWORDS:

        if keyword in name_lower:
            return "CRIME CATEGORY"

    # Current FIR network uses accused entities
    # as the source of these relationships.
    if (
        "REPORTED_AGAINST" in relationships
        or "INVOLVED_IN_CRIME" in relationships
        or "CHARGED_UNDER" in relationships
        or "CASE_REGISTERED_AT" in relationships
        or "LOCATED_IN_STATE" in relationships
        or "LOCATED_IN_DISTRICT" in relationships
    ):
        return "PERSON"

    return "ENTITY"


# ============================================================
# SELECT IMPORTANT NODES
# ============================================================

degree_list = sorted(
    G.degree(),
    key=lambda item: item[1],
    reverse=True
)

selected_nodes = [
    node
    for node, degree
    in degree_list[:MAX_NODES]
]

H = G.subgraph(
    selected_nodes
).copy()

print(
    "Visualization nodes:",
    H.number_of_nodes()
)

print(
    "Visualization relationships:",
    H.number_of_edges()
)


# ============================================================
# CREATE PYVIS NETWORK
# ============================================================

net = Network(
    height="800px",
    width="100%",
    bgcolor="#0b1020",
    font_color="#e5e7eb",
    directed=False,
    notebook=False
)


# ============================================================
# PHYSICS
# ============================================================

net.barnes_hut(
    gravity=-5000,
    central_gravity=0.15,
    spring_length=190,
    spring_strength=0.025,
    damping=0.15,
    overlap=0.2
)


# ============================================================
# ADD NODES
# ============================================================

for node in H.nodes():

    node_name = str(node)

    degree = H.degree(node)

    entity_type = detect_entity_type(
        node_name
    )

    # ----------------------------------------
    # Node size
    # ----------------------------------------

    node_size = min(
        max(
            10 + degree * 1.4,
            10
        ),
        34
    )

    # ----------------------------------------
    # Visual category
    # ----------------------------------------

    if entity_type == "PERSON":

        shape = "dot"

        color = {
            "background": "#2563eb",
            "border": "#93c5fd",
            "highlight": {
                "background": "#60a5fa",
                "border": "#ffffff"
            }
        }

    elif entity_type == "STATE":

        shape = "diamond"

        color = {
            "background": "#7c3aed",
            "border": "#c4b5fd",
            "highlight": {
                "background": "#a78bfa",
                "border": "#ffffff"
            }
        }

    elif entity_type == "CRIME CATEGORY":

        shape = "square"

        color = {
            "background": "#dc2626",
            "border": "#fca5a5",
            "highlight": {
                "background": "#f87171",
                "border": "#ffffff"
            }
        }

    elif entity_type == "LEGAL SECTION":

        shape = "triangle"

        color = {
            "background": "#d97706",
            "border": "#fcd34d",
            "highlight": {
                "background": "#fbbf24",
                "border": "#ffffff"
            }
        }

    else:

        shape = "ellipse"

        color = {
            "background": "#059669",
            "border": "#6ee7b7",
            "highlight": {
                "background": "#34d399",
                "border": "#ffffff"
            }
        }

    # ----------------------------------------
    # Keep graph clean
    # ----------------------------------------

    if degree >= 8:
        label = node_name
    else:
        label = ""

    # ----------------------------------------
    # Tooltip
    # ----------------------------------------

    safe_name = html.escape(
        node_name
    )

    tooltip = (
        "<div style='"
        "font-family:Arial;"
        "padding:8px;"
        "line-height:1.6;"
        "'>"
        "<b>Entity</b><br>"
        + safe_name
        + "<br><br>"
        "<b>Type</b><br>"
        + entity_type
        + "<br><br>"
        "<b>Connections in view</b><br>"
        + str(degree)
        + "</div>"
    )

    net.add_node(
        node,
        label=label,
        title=tooltip,
        shape=shape,
        size=node_size,
        color=color,
        borderWidth=1.5,
        borderWidthSelected=4,
        font={
            "size": 13,
            "face": "Arial",
            "color": "#e5e7eb",
            "strokeWidth": 2,
            "strokeColor": "#0b1020"
        }
    )


# ============================================================
# ADD EDGES
# ============================================================

for source, target, data in H.edges(
    data=True
):

    relationship = str(
        data.get(
            "relationship",
            "CONNECTED_TO"
        )
    )

    safe_relationship = html.escape(
        relationship
    )

    edge_tooltip = (
        "<div style='"
        "font-family:Arial;"
        "padding:6px;"
        "'>"
        "<b>Relationship</b><br>"
        + safe_relationship
        + "</div>"
    )

    net.add_edge(
        source,
        target,
        title=edge_tooltip,
        label="",
        width=1,
        color={
            "color": "rgba(148,163,184,0.35)",
            "highlight": "#60a5fa",
            "hover": "#94a3b8"
        },
        selectionWidth=3
    )


# ============================================================
# NETWORK OPTIONS
# ============================================================

net.set_options(
    """
    {
        "nodes": {
            "shape": "dot",
            "scaling": {
                "min": 8,
                "max": 34
            },
            "font": {
                "size": 13,
                "face": "Arial",
                "color": "#e5e7eb",
                "strokeWidth": 2,
                "strokeColor": "#0b1020"
            }
        },

        "edges": {
            "smooth": {
                "enabled": true,
                "type": "dynamic"
            },
            "width": 1,
            "selectionWidth": 3,
            "color": {
                "inherit": false,
                "opacity": 0.35
            }
        },

        "interaction": {
            "hover": true,
            "hoverConnectedEdges": true,
            "selectConnectedEdges": true,
            "multiselect": false,
            "navigationButtons": true,
            "keyboard": {
                "enabled": true
            },
            "zoomView": true,
            "dragView": true,
            "dragNodes": true
        },

        "physics": {
            "enabled": true,
            "solver": "barnesHut",

            "stabilization": {
                "enabled": true,
                "iterations": 250,
                "updateInterval": 25,
                "onlyDynamicEdges": false,
                "fit": true
            },

            "barnesHut": {
                "gravitationalConstant": -5000,
                "centralGravity": 0.15,
                "springLength": 190,
                "springConstant": 0.025,
                "damping": 0.15,
                "avoidOverlap": 0.2
            },

            "minVelocity": 0.75,
            "timestep": 0.5
        }
    }
    """
)


# ============================================================
# CREATE HTML
# ============================================================

os.makedirs(
    "output",
    exist_ok=True
)

net.write_html(
    OUTPUT_FILE,
    open_browser=False
)


# ============================================================
# LOAD GENERATED HTML
# ============================================================

with open(
    OUTPUT_FILE,
    "r",
    encoding="utf-8"
) as file:

    page = file.read()


# ============================================================
# SEARCH DATA
# ============================================================

search_data = []

for node in H.nodes():

    name = str(node)

    search_data.append(
        {
            "id": str(node),
            "name": name,
            "type": detect_entity_type(name),
            "connections": int(H.degree(node))
        }
    )

search_json = json.dumps(
    search_data
)


# ============================================================
# INVESTIGATOR PANEL
# ============================================================

panel = """
<style>

#investigator-panel {
    position: absolute;
    top: 15px;
    left: 15px;

    z-index: 9999;

    width: 300px;

    padding: 16px;

    background: rgba(15, 23, 42, 0.96);

    border: 1px solid rgba(148, 163, 184, 0.25);

    border-radius: 12px;

    color: #e5e7eb;

    font-family: Arial, sans-serif;

    box-shadow:
        0 10px 30px rgba(0, 0, 0, 0.35);
}

#investigator-title {
    font-size: 17px;
    font-weight: 700;
    margin-bottom: 4px;
}

#investigator-subtitle {
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 14px;
}

#entity-search {
    width: 100%;
    box-sizing: border-box;

    padding: 10px;

    background: #020617;

    color: #e5e7eb;

    border: 1px solid #334155;

    border-radius: 8px;

    outline: none;
}

#entity-search:focus {
    border-color: #60a5fa;
}

#search-results {
    margin-top: 8px;

    max-height: 180px;

    overflow-y: auto;
}

.search-result {
    padding: 8px;

    margin-bottom: 4px;

    border-radius: 6px;

    cursor: pointer;

    background: rgba(51, 65, 85, 0.45);
}

.search-result:hover {
    background: rgba(59, 130, 246, 0.25);
}

.result-name {
    font-weight: 600;
    font-size: 13px;
}

.result-type {
    color: #94a3b8;
    font-size: 11px;
}

#selected-entity {
    margin-top: 14px;

    padding-top: 12px;

    border-top: 1px solid #334155;

    font-size: 12px;

    color: #cbd5e1;
}

.entity-value {
    color: #f8fafc;

    font-weight: 600;
}

#network-legend {
    margin-top: 14px;

    padding-top: 12px;

    border-top: 1px solid #334155;
}

.legend-row {
    display: flex;

    align-items: center;

    margin: 7px 0;

    font-size: 12px;
}

.legend-dot {
    width: 12px;
    height: 12px;

    margin-right: 8px;

    border-radius: 50%;
}

.legend-diamond {
    width: 11px;
    height: 11px;

    margin-right: 9px;

    transform: rotate(45deg);
}

.legend-square {
    width: 11px;
    height: 11px;

    margin-right: 9px;
}

</style>

<div id="investigator-panel">

    <div id="investigator-title">
        Investigation Network
    </div>

    <div id="investigator-subtitle">
        Interactive entity relationship analysis
    </div>

    <input
        id="entity-search"
        type="text"
        placeholder="Search person or entity..."
        autocomplete="off"
    >

    <div id="search-results"></div>

    <div id="selected-entity">
        Select a node to inspect its network.
    </div>

    <div id="network-legend">

        <div class="legend-row">
            <div
                class="legend-dot"
                style="background:#2563eb;"
            ></div>
            Person
        </div>

        <div class="legend-row">
            <div
                class="legend-diamond"
                style="background:#7c3aed;"
            ></div>
            State
        </div>

        <div class="legend-row">
            <div
                class="legend-square"
                style="background:#dc2626;"
            ></div>
            Crime category
        </div>

        <div class="legend-row">
            <div
                style="
                    width:0;
                    height:0;
                    border-left:7px solid transparent;
                    border-right:7px solid transparent;
                    border-bottom:12px solid #d97706;
                    margin-right:8px;
                "
            ></div>
            Legal section
        </div>

        <div class="legend-row">
            <div
                class="legend-dot"
                style="background:#059669;"
            ></div>
            Other entity
        </div>

    </div>

</div>
"""


# ============================================================
# SEARCH JAVASCRIPT
# ============================================================

search_script = """
<script>

const investigatorNodes = __NODE_DATA__;

const searchInput =
    document.getElementById(
        "entity-search"
    );

const searchResults =
    document.getElementById(
        "search-results"
    );

const selectedEntity =
    document.getElementById(
        "selected-entity"
    );


function escapeHtml(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function showEntityInfo(nodeId) {

    const entity =
        investigatorNodes.find(
            function(item) {
                return String(item.id) === String(nodeId);
            }
        );

    if (!entity) {
        return;
    }

    selectedEntity.innerHTML =
        "<div><b>Selected entity</b></div>" +

        "<div style='margin-top:8px;'>" +
        "Name: " +
        "<span class='entity-value'>" +
        escapeHtml(entity.name) +
        "</span>" +
        "</div>" +

        "<div style='margin-top:5px;'>" +
        "Type: " +
        "<span class='entity-value'>" +
        escapeHtml(entity.type) +
        "</span>" +
        "</div>" +

        "<div style='margin-top:5px;'>" +
        "Connections: " +
        "<span class='entity-value'>" +
        entity.connections +
        "</span>" +
        "</div>";
}


function focusEntity(nodeId) {

    if (
        typeof network === "undefined"
    ) {
        return;
    }

    network.selectNodes(
        [nodeId]
    );

    network.focus(
        nodeId,
        {
            scale: 1.35,

            animation: {
                duration: 700,
                easingFunction: "easeInOutQuad"
            }
        }
    );

    showEntityInfo(nodeId);
}


searchInput.addEventListener(
    "input",
    function() {

        const query =
            this.value
                .trim()
                .toLowerCase();

        searchResults.innerHTML = "";

        if (!query) {
            return;
        }

        const matches =
            investigatorNodes
                .filter(
                    function(item) {
                        return item.name
                            .toLowerCase()
                            .includes(query);
                    }
                )
                .sort(
                    function(a, b) {
                        return b.connections -
                            a.connections;
                    }
                )
                .slice(0, 12);

        matches.forEach(
            function(entity) {

                const result =
                    document.createElement(
                        "div"
                    );

                result.className =
                    "search-result";

                result.innerHTML =
                    "<div class='result-name'>" +
                    escapeHtml(entity.name) +
                    "</div>" +

                    "<div class='result-type'>" +
                    escapeHtml(entity.type) +
                    " · " +
                    entity.connections +
                    " connections" +
                    "</div>";

                result.addEventListener(
                    "click",
                    function() {

                        focusEntity(
                            entity.id
                        );

                        searchInput.value =
                            entity.name;

                        searchResults.innerHTML =
                            "";
                    }
                );

                searchResults.appendChild(
                    result
                );
            }
        );
    }
);


setTimeout(
    function() {

        if (
            typeof network === "undefined"
        ) {
            return;
        }

        network.on(
            "selectNode",
            function(params) {

                if (
                    params.nodes &&
                    params.nodes.length > 0
                ) {

                    showEntityInfo(
                        params.nodes[0]
                    );
                }
            }
        );

    },
    1000
);

</script>
"""


# ============================================================
# INSERT DATA SAFELY
# ============================================================

search_script = search_script.replace(
    "__NODE_DATA__",
    search_json
)


# ============================================================
# INSERT INVESTIGATOR UI
# ============================================================

page = page.replace(
    "<body>",
    "<body>" + panel + search_script,
    1
)


# ============================================================
# SAVE FINAL HTML
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write(page)


# ============================================================
# FINAL STATUS
# ============================================================

print("\n======================================")
print(" NETWORK VISUALIZATION CREATED")
print("======================================")

print(
    "Original nodes:",
    G.number_of_nodes()
)

print(
    "Original relationships:",
    G.number_of_edges()
)

print(
    "Visualization nodes:",
    H.number_of_nodes()
)

print(
    "Visualization relationships:",
    H.number_of_edges()
)

print(
    "Output file:",
    OUTPUT_FILE
)

print("\nInvestigator features:")

print(" - Person/entity distinction")
print(" - State distinction")
print(" - Crime category distinction")
print(" - Legal section distinction")
print(" - Interactive node selection")
print(" - Connected-node highlighting")
print(" - Entity search")
print(" - Focus and zoom")
print(" - Hover intelligence")
print(" - Investigator legend")
print(" - Optimized physics")
print(" - 300-node browser view")