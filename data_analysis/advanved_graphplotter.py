import argparse
import math
from pathlib import Path

import networkx as nx
from networkx.drawing.nx_pydot import read_dot, write_dot


def clean(name):
    return str(name).strip('"')


def shorten(name):
    if name.startswith("app-"):
        parts = name.split("-")
        # app-<n>-<type>-<hash>-<id> → app-<n>-<type>-<xx>
        if len(parts) >= 5:
            return f"{parts[0]}-{parts[1]}-{parts[2]}-{parts[-1][-2:]}"
    elif name.startswith("apiserver"):
        parts = name.split("-")
        # apiserver-<hash>-<id> → apiserver-<xx>
        if len(parts) >= 3:
            return f"{parts[0]}-{parts[-1][-2:]}"
    return name


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
            angle = 2 * math.pi * i / max(n, 1) + 20
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
    output_path = Path(args.output) if args.output else input_path

    G = read_dot(input_path)
    G = nx.relabel_nodes(G, lambda x: clean(x))

    pos = build_layout(G)
    # rename nodes
    mapping = {n: shorten(n) for n in G.nodes}
    G = nx.relabel_nodes(G, mapping)

    # remap positions
    pos = {mapping[n]: p for n, p in pos.items()}

    # write positions back
    for node, (x, y) in pos.items():
        sx, sy = x * 200, y * 200
        G.nodes[node]["pos"] = f"{sx},{sy}!"
        G.nodes[node]["pin"] = "true"
    for u, v, data in G.edges(data=True):
        edge_type = str(data.get("type", "")).strip('"')
        if edge_type == "connection":
            latency = float(str(data.get("latency", "0")).strip('"'))
            throughput = float(str(data.get("throughput", "0")).strip('"'))

            # fix scaling: convert to kbps
            kbps = throughput / 1000.0

            data["label"] = f"{int(latency)}ms {int(kbps)}kbps"
            data["throughput"] = str(int(kbps))
    write_dot(G, output_path)
    print(f"Wrote positioned graph to {output_path}")


if __name__ == "__main__":
    main()
