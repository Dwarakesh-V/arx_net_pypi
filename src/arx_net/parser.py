import re

# Parse Arx-Net style edges
def _split_top_level(input_str):
    result = []
    depth = 0
    current = ''
    for char in input_str:
        if char == '(':
            depth += 1
        if char == ')':
            depth -= 1
        if char == ',' and depth == 0:
            result.append(current)
            current = ''
        else:
            current += char
    result.append(current)
    return [s for s in result if s.strip() != '']

def parse_edges(edges_input, directed=True, strict=False):
    """
    Parse the arx net application format into a python compatible adjacency list format.

    Args:
        edges_input : Arx-Tet type input edge format
        directed : Directed or Undirected
        strict : Continue or terminate for invalid cases

    Returns:
        Python compatible adjacency list of type dict.
    """
    simple_format = re.compile(r'^([a-zA-Z0-9]{2})(-?\d*\.?\d*)$')
    paren_format = re.compile(r'^\(\s*([a-zA-Z0-9]+)\s*,\s*([a-zA-Z0-9]+)\s*(?:,\s*(-?\d*\.?\d*)\s*)?\)$')

    edges_raw = []
    for edge in _split_top_level(edges_input):
        edge = edge.strip()

        source = target = weight = None

        if m := simple_format.match(edge):
            source = m.group(1)[0]
            target = m.group(1)[1]
            w = m.group(2)
            weight = float(w) if w else None
        elif m := paren_format.match(edge):
            source = m.group(1)
            target = m.group(2)
            w = m.group(3)
            weight = float(w) if w else None
        elif len(edge) == 1:
            source = edge
            target = None
            weight = None
        else:
            if strict:
                raise ValueError(f"Invalid edge format: {edge}")
            continue

        if weight is None or (isinstance(weight, float) and weight != weight):  # NaN check
            weight = None  # keep as None rather than defaulting to 1, so we know if weights are absent

        edges_raw.append({'source': source, 'target': target, 'weight': weight})

    # Remove duplicates, keeping last occurrence
    edge_map = {}
    for edge in edges_raw:
        if edge['source'] and edge['target']:
            key = f"{edge['source']}_{edge['target']}"
            edge_map[key] = edge
            if not directed:
                reverse_key = f"{edge['target']}_{edge['source']}"
                if reverse_key in edge_map:
                    del edge_map[reverse_key]

    edges_raw = list(edge_map.values())

    has_weights = any(e['weight'] is not None for e in edges_raw)

    adj = {}
    for edge in edges_raw:
        src, tgt, w = edge['source'], edge['target'], edge['weight']
        if src is None:
            continue

        for node in ([src, tgt] if tgt else [src]):
            if node not in adj:
                adj[node] = []

        if tgt is not None:
            neighbor = (tgt, w if w is not None else 1) if has_weights else tgt
            adj[src].append(neighbor)

            if not directed:
                neighbor_rev = (src, w if w is not None else 1) if has_weights else src
                adj[tgt].append(neighbor_rev)

    return adj

