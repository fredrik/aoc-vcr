"""Auto-detection and serialization of common AoC data structures."""

from typing import Any


def is_grid(obj: Any) -> bool:
    """Check if obj is a dict with (int, int) tuple keys."""
    if not isinstance(obj, dict) or not obj:
        return False
    for key in obj:
        if not (isinstance(key, tuple) and len(key) == 2 and
                isinstance(key[0], int) and isinstance(key[1], int)):
            return False
    return True


def is_point_collection(obj: Any) -> bool:
    """Check if obj is a set/list of tuples."""
    if not isinstance(obj, (set, list)) or not obj:
        return False
    sample = next(iter(obj))
    return isinstance(sample, tuple) and all(isinstance(x, (int, float)) for x in sample)


def is_graph(obj: Any) -> bool:
    """Check if obj is a dict with list values (adjacency list)."""
    if not isinstance(obj, dict) or not obj:
        return False
    for value in obj.values():
        if not isinstance(value, list):
            return False
    return True


def serialize_grid(grid: dict[tuple[int, int], Any]) -> dict:
    """Serialize a grid dict to sparse format with bounds."""
    if not grid:
        return {"type": "grid", "data": {}, "bounds": None}

    rows = [k[0] for k in grid]
    cols = [k[1] for k in grid]

    return {
        "type": "grid",
        "data": {f"{r},{c}": v for (r, c), v in grid.items()},
        "bounds": {
            "min_row": min(rows),
            "max_row": max(rows),
            "min_col": min(cols),
            "max_col": max(cols),
        },
    }


def serialize_points(points: set | list) -> dict:
    """Serialize a point collection."""
    return {
        "type": "points",
        "data": [list(p) for p in points],
    }


def serialize_graph(graph: dict) -> dict:
    """Serialize an adjacency list graph."""
    nodes = set(graph.keys())
    for neighbors in graph.values():
        nodes.update(neighbors)

    edges = []
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            edges.append([node, neighbor])

    return {
        "type": "graph",
        "nodes": list(nodes),
        "edges": edges,
    }


def serialize_value(value: Any) -> Any:
    """Auto-detect type and serialize appropriately."""
    if is_grid(value):
        return serialize_grid(value)
    if is_point_collection(value):
        return serialize_points(value)
    if is_graph(value):
        return serialize_graph(value)
    return value
