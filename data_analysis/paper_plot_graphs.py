import re
import sys


def parse_attrs(attr_str):
    attrs = {}
    # Match key="value" (with commas inside) or key=value
    parts = re.findall(r'\w+\s*=\s*"[^"]*"|\w+\s*=\s*[^,]+', attr_str)
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            attrs[k.strip()] = v.strip()
    return attrs


def build_attrs(attrs):
    return ", ".join(f"{k}={v}" for k, v in attrs.items())


def transform_dot(input_path):
    with open(input_path) as f:
        lines = f.readlines()

    out = []
    edges = {}
    other_lines = []

    edge_pattern = re.compile(r'^"([^"]+)" -> "([^"]+)" \[(.*)\];')

    for line in lines:
        # Node
        m_node = re.match(r'^"([^"]+)" \[(.*)\];', line)
        if m_node:
            name, attr_str = m_node.groups()
            attrs = parse_attrs(attr_str)

            # --- SIZE / SHAPE ---
            if name in {"worker-0", "worker-5", "worker-6"}:
                attrs.update(
                    {
                        "shape": '"square"',
                        "width": "0.4",
                        "height": "0.4",
                        "fixedsize": "true",
                        "label": f'"{name.split("-")[0]}\\n{name.split("-")[1]}"',
                    }
                )
            elif name in {"worker-1", "worker-3", "worker-4"}:
                attrs.update(
                    {
                        "shape": '"square"',
                        "width": "0.6",
                        "height": "0.6",
                        "fixedsize": "true",
                        "label": f'"{name.split("-")[0]}\\n{name.split("-")[1]}"',
                    }
                )
            elif name in {"manager-0", "worker-2"}:
                attrs.update(
                    {
                        "shape": '"rect"',
                        "width": "1.2",
                        "height": "0.6",
                        "fixedsize": "true",
                    }
                )

            # --- COLOR ---
            if name.startswith("app-2"):
                attrs.update(
                    {"colorscheme": '"reds3"', "fillcolor": '"1"', "color": '"2"'}
                )
            if name.startswith("apiserver"):
                attrs.update(
                    {"colorscheme": '"greys3"', "fillcolor": '"2"', "color": '"2"'}
                )

            new_line = f'"{name}" [{build_attrs(attrs)}];\n'
            out.append(new_line)
            continue

        # Edge
        m_edge = edge_pattern.match(line)
        if m_edge:
            src, dst, attr_str = m_edge.groups()
            key = tuple(sorted([src, dst]))
            if key in edges:
                # Merge → bidirectional
                edges[key]["attrs"]["dir"] = "both"
            else:
                edges[key] = {
                    "src": src,
                    "dst": dst,
                    "attrs": parse_attrs(attr_str),
                }
            continue

        # Other lines (graph-level attributes)
        other_lines.append(line)

    # Write graph-level stuff
    out.extend(other_lines)

    # Write edges
    for e in edges.values():
        line = f'"{e["src"]}" -> "{e["dst"]}" [{build_attrs(e["attrs"])}];\n'
        out.append(line)

    with open(input_path, "w") as f:
        f.writelines(out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py input.dot")
        sys.exit(1)
    transform_dot(sys.argv[1])
