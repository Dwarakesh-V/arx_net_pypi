# Arx-Net

A lightweight Python library for parsing graph edge strings and converting
between common graph representations.

## Installation

```bash
pip install arx-net
```

## Features

- Parse edge strings
- Directed and undirected graphs
- Weighted and unweighted graphs
- Convert between

  - adjacency lists
  - edge lists
  - adjacency matrices

## Example

```python
import arx_net

graph = arx_net.parse_edges(
    "(A,B,4),(B,C,2),(C,D)"
)

print(graph)
```

Output

```python
{
    "A": [("B",4)],
    "B": [("C",2)],
    "C": [("D",1)],
    "D": []
}
```

Convert formats

```python
edges = arx_net.convert_type(graph, "edge")
matrix, order = arx_net.convert_type(graph, "matrix")
```

## Supported formats

### Adjacency List

```python
{
    "A": ["B", "C"]
}
```

### Edge List

```python
[
    ("A","B"),
    ("A","C")
]
```

### Matrix

```python
[
 [0,1,1],
 [0,0,1],
 [0,0,0]
]
```

## License

MIT