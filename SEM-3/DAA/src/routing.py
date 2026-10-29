"""Nearest-neighbor TSP approximation over shortest-road-path distances."""
from .graph import RoadGraph


def nearest_neighbor_route(graph: RoadGraph, depot: str, stops: list[str],
                           paths_from_depot: dict[str, tuple[float, tuple[str, ...]]] | None = None
                           ) -> tuple[tuple[str, ...], tuple[str, ...], float]:
    """Visit each unique stop once, return to depot, and expand legs to road nodes.

    Tie breaks lexically. The heuristic is O(k^2) after pairwise distances are known.
    """
    if depot not in graph.adjacency:
        raise ValueError(f"Unknown depot: {depot}")
    remaining = set(stops) - {depot}
    for stop in remaining:
        if stop not in graph.adjacency:
            raise ValueError(f"Unknown stop: {stop}")
    nodes = sorted(remaining | {depot})
    pair_paths: dict[tuple[str, str], tuple[float, tuple[str, ...]]] = {}
    for source in nodes:
        if source == depot and paths_from_depot is not None:
            for target in nodes:
                if target != depot and target in paths_from_depot:
                    pair_paths[(source, target)] = paths_from_depot[target]
            pair_paths[(source, source)] = (0.0, (source,))
        else:
            dist, prev = graph.dijkstra(source)
            for target in nodes:
                if target in dist and dist[target] != float("inf"):
                    pair_paths[(source, target)] = (dist[target], graph.reconstruct_path(target, dist, prev))
    def leg(a: str, b: str) -> tuple[float, tuple[str, ...]]:
        if (a, b) in pair_paths:
            return pair_paths[(a, b)]
        d, p = pair_paths[(b, a)]
        return d, tuple(reversed(p))

    order = [depot]
    current = depot
    total = 0.0
    expanded = [depot]
    while remaining:
        next_stop = min(remaining, key=lambda stop: (leg(current, stop)[0], stop))
        distance, path = leg(current, next_stop)
        total += distance
        expanded.extend(path[1:])
        order.append(next_stop)
        remaining.remove(next_stop)
        current = next_stop
    if current != depot:
        distance, path = leg(current, depot)
        total += distance
        expanded.extend(path[1:])
        order.append(depot)
    return tuple(order), tuple(expanded), total
