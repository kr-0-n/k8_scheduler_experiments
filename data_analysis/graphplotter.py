import argparse
import networkx as nx
import matplotlib.pyplot as plt
import math
from pathlib import Path


def clean(name):
    return str(name).strip('"')


def build_layout(G):
    pos = {
        "worker-5": (0, 1),
        "worker-0": (1, 1),
        "worker-1": (2, 1),
        "worker-4": (3, 1),
        "worker-6": (0, 0),
        "manager-0": (1, 0),
        "worker-2": (2, 0),
        "worker-3": (3, 0),
    }

    worker_pods = {}

    for u, v, data in G.edges(data=True):
        edge_type = str(data.get("type", "")).strip('"')
        if edge_type == "assign":
            worker_pods.setdefault(v, []).append(u)

    radius = 0.25

    for worker, pods in worker_pods.items():
        if worker not in pos:
            continue

        wx, wy = pos[worker]
        n = len(pods)

        for i, pod in enumerate(pods):
            angle = 2 * math.pi * i / max(n, 1)
            px = wx + radius * math.cos(angle)
            py = wy + radius * math.sin(angle)
            pos[pod] = (px, py)

    for n in G.nodes:
        if n not in pos:
            pos[n] = (0, -0.5)

    return pos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dot")
    parser.add_argument("-o", "--output")
    args = parser.parse_args()

    input_path = Path(args.input_dot)
    output_path = args.output or input_path.with_suffix(".png")

    G = nx.drawing.nx_pydot.read_dot(input_path)

    # normalize node names
    G = nx.relabel_nodes(G, lambda x: clean(x))

    pos = build_layout(G)

    workers = [n for n in G.nodes if n.startswith("worker")]
    managers = [n for n in G.nodes if n.startswith("manager")]
    pods = [n for n in G.nodes if n.startswith("app")]

    connection_edges = []
    assign_edges = []

    for u, v, data in G.edges(data=True):
        edge_type = str(data.get("type", "")).strip('"')
        if edge_type == "assign":
            assign_edges.append((u, v))
        else:
            connection_edges.append((u, v))

    plt.figure(figsize=(10, 6))

    nx.draw_networkx_nodes(
        G, pos, nodelist=workers, node_color="#87CEEB", node_size=1400
    )
    nx.draw_networkx_nodes(
        G, pos, nodelist=managers, node_color="#FFD166", node_size=1600
    )
    nx.draw_networkx_nodes(G, pos, nodelist=pods, node_color="#EF476F", node_size=600)

    nx.draw_networkx_edges(G, pos, edgelist=connection_edges, width=2)
    nx.draw_networkx_edges(G, pos, edgelist=assign_edges, style="dashed", alpha=0.6)

    nx.draw_networkx_labels(G, pos, font_size=8)

    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print("Saved to", output_path)


if __name__ == "__main__":
    main()
