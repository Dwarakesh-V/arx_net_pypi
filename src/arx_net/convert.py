from warnings import warn

# Type conversion
# Parse to canonical edges
def _parse_adj(adj):
    nodes = set(adj.keys())
    edges = []
    for src, neighbors in adj.items():
        for nb in neighbors:
            if isinstance(nb, (tuple, list)) and len(nb) == 2:
                tgt, w = nb
            else:
                tgt, w = nb, None
            nodes.add(tgt)
            edges.append((src, tgt, w))
    return edges, nodes

def _parse_edge_list(edge_list):
    nodes = set()
    edges = []
    for e in edge_list:
        if isinstance(e, dict):
            src = e.get('source', e.get('src'))
            tgt = e.get('target', e.get('tgt'))
            w   = e.get('weight', e.get('w'))
        elif len(e) == 3:
            src, tgt, w = e
        elif len(e) == 2:
            src, tgt, w = *e, None
        else:
            warn(f"Skipping malformed edge: {e}")
            continue
        if src is None or tgt is None:
            warn(f"Skipping edge with missing src/tgt: {e}")
            continue
        nodes.update([src, tgt])
        edges.append((src, tgt, w))
    return edges, nodes

def _parse_matrix(matrix):
    edges = []
    if isinstance(matrix, dict):
        nodes = set(matrix.keys())
        for src, row in matrix.items():
            for tgt, val in row.items():
                nodes.add(tgt)
                if val != 0:
                    edges.append((src, tgt, val))
    else:
        n = len(matrix)
        nodes = set(range(n))
        for i, row in enumerate(matrix):
            for j, val in enumerate(row):
                if val != 0:
                    edges.append((i, j, val))
    return edges, nodes

def convert_type(input_graph, to, directed=None, weighted=None, from_type=None):
    """
    Convert between graph representations seamlessly.

    Args:
        input_graph : Input graph in any supported format -
            Adjacency list  : { node: [neighbor, ...] } or { node: [(neighbor, weight), ...] }
            Edge list       : [(src, tgt), ...] or [(src, tgt, weight), ...]
                              or list of dicts with 'source'/'target'/'weight' keys (parse_edges output)
            Matrix          : 2D list  (nodes = row/col indices)
                              or dict-of-dicts { src: { tgt: weight } }
        to          : Target format - 'adj', 'edge', or 'matrix'
        directed    : bool. Auto-detected from input symmetry if None.
        weighted    : bool. Auto-detected from input structure if None.
        from_type   : Input format - 'adj', 'edge', or 'matrix'. Auto-detected if None.
                      ('from' is a Python keyword, so from_type is used instead.)

    Returns:
        'adj'
            {node: [neighbor, ...]} or
            {node: [(neighbor, weight), ...]}

        'edge'
            [(src, tgt), ...] or
            [(src, tgt, weight), ...]

        'matrix'
            (2D list, node_order)
            node_order[i] gives the label for row/column i.

    Notes:
        - For binary (0/1) matrices, weighted is inferred as False since 1 = "edge exists".
          If your graph genuinely has weight=1 on all edges, pass weighted=True explicitly.
        - Directed detection is a heuristic: if every edge (u,v) has a reverse (v,u), 
          the graph is assumed undirected. Pass directed=True/False to override.
    """

    FORMAT_ALIASES = {
        'adj': 'adj', 'adjacency_list': 'adj', 'adjacency': 'adj',
        'edge': 'edge', 'edge_list': 'edge', 'edges': 'edge',
        'matrix': 'matrix', 'adjacency_matrix': 'matrix', 'mat': 'matrix',
    }

    to = FORMAT_ALIASES.get(to, to)
    if to not in ('adj', 'edge', 'matrix'):
        raise ValueError(f"Unknown target format '{to}'. Use 'adj', 'edge', or 'matrix'.")

    if from_type is not None:
        from_type = FORMAT_ALIASES.get(from_type, from_type)

    # Auto-detect input format
    def detect_format(g):
        if isinstance(g, dict):
            if not g:
                return 'adj'
            first_val = next(iter(g.values()))
            return 'matrix' if isinstance(first_val, dict) else 'adj'
        if isinstance(g, list):
            if not g:
                return 'edge'
            return 'matrix' if isinstance(g[0], list) else 'edge'
        raise ValueError("Cannot auto-detect format. Specify `from_type` explicitly.")

    fmt = from_type if from_type is not None else detect_format(input_graph)
    if fmt not in ('adj', 'edge', 'matrix'):
        raise ValueError(f"Unknown input format '{fmt}'.")

    parsers = {'adj': _parse_adj, 'edge': _parse_edge_list, 'matrix': _parse_matrix}
    edges, nodes = parsers[fmt](input_graph)

    # Auto-detect weighted
    if weighted is None:
        if fmt == 'matrix':
            # Binary 0/1 matrix → unweighted; any other value → weighted
            weighted = any(w not in (0, 1) for _, _, w in edges)
        else:
            weighted = any(w is not None for _, _, w in edges)

    # Auto-detect directed
    if directed is None:
        if fmt == 'matrix' and isinstance(input_graph, list):
            n = len(input_graph)
            directed = any(
                input_graph[i][j] != input_graph[j][i]
                for i in range(n) for j in range(i, n)
            )
        else:
            edge_set = {(s, t) for s, t, _ in edges}
            directed = not all(
                (t, s) in edge_set
                for s, t, _ in edges if s != t
            )

    # Normalize
    if weighted:
        edges = [(s, t, w if w is not None else 1) for s, t, w in edges]
    else:
        edges = [(s, t, None) for s, t, _ in edges]

    if not directed:
        seen = set()
        deduped = []
        for s, t, w in edges:
            key = frozenset([s, t])
            if key not in seen:
                seen.add(key)
                deduped.append((s, t, w))
        edges = deduped

    # Build target format

    def build_adj(edges, nodes, directed, weighted):
        adj = {n: [] for n in nodes}
        for s, t, w in edges:
            adj.setdefault(s, []).append((t, w) if weighted else t)
            if not directed:
                adj.setdefault(t, []).append((s, w) if weighted else s)
        return adj

    def build_edge_list(edges, weighted):
        return [(s, t, w) if weighted else (s, t) for s, t, w in edges]

    def build_matrix(edges, nodes, directed, weighted):
        node_order = sorted(nodes, key=str)
        idx = {n: i for i, n in enumerate(node_order)}
        size = len(node_order)
        matrix = [[0] * size for _ in range(size)]
        for s, t, w in edges:
            val = w if weighted else 1
            matrix[idx[s]][idx[t]] = val
            if not directed:
                matrix[idx[t]][idx[s]] = val
        return matrix, node_order

    builders = {
        'adj':    lambda: build_adj(edges, nodes, directed, weighted),
        'edge':   lambda: build_edge_list(edges, weighted),
        'matrix': lambda: build_matrix(edges, nodes, directed, weighted),
    }
    return builders[to]()