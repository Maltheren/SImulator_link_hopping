import numpy as np
import numpy.typing as npt
import pandas as pd
from typing import Tuple        ##Bruger vi så vi kan få syntax highlighting
from typing import List, Tuple, Union
from numba import njit          ##accelering


def construct_adjacencylist(rx: list[str], tx: list[str], weights: list[float]) -> dict[str, list[tuple[str, float]]]:
    output_dict = {}

    for t, r, w in zip(tx, rx, weights):
        if t not in output_dict:
            output_dict[t] = []
        output_dict[t].append((r, w))  # store tuple (receiver, weight)

    return output_dict


PathType = List[Union[str, Tuple[str, float, str]]]
PathSet = List[PathType]


##En sindssyg runner der finder alle possible paths
def all_paths(graph, start, end, path=None) -> PathSet:
    """
    Finds all possible acyclic paths from start to end in a weighted graph,
    where each path includes edges with weights.
    
    graph: dict where graph[node] = list of (neighbor, weight)
    """
    if path is None:
        path = []

    # If path is empty, we start with a placeholder for the first node
    if not path:
        path = [start]

    # If we've reached the target, return the path as-is
    if start == end:
        return [path]

    paths = []
    for neighbor, weight in graph.get(start, []):
        # Avoid cycles by checking nodes in the path (only check the last nodes)
        nodes_in_path = [e[0] if isinstance(e, tuple) else e for e in path]
        if neighbor not in nodes_in_path:
            # Extend path with edge info
            new_path = path + [(start, weight, neighbor)]
            paths.extend(all_paths(graph, neighbor, end, new_path))
    return paths


def find_worst_link(path: PathType) -> float:
    minimum = np.inf
    for edge in path:
        if isinstance(edge, tuple) and len(edge) == 3:
            # edge = (from_node, weight, to_node)
            minimum = min(minimum, edge[1])
    return minimum


if __name__ == "__main__":
    tx = ['A', 'C', 'B', 'B']
    rx = ['C', 'B', 'C', 'D']
    snr = ['-20', '-30', '-25', '-40']

    adj_list = construct_adjacencylist(rx, tx, snr)
    paths = all_paths(adj_list, "A", "B")
    print(adj_list)
    print(paths)