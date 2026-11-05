"""Weighted undirected road graph and Dijkstra shortest paths."""
from heapq import heappop, heappush
from math import inf, isfinite


class RoadGraph:
    def __init__(self, nodes: list[str], edges: list[dict]):
        if len(nodes) != len(set(nodes)):
            raise ValueError("graph node IDs must be unique")
        self.nodes = tuple(nodes)
        self.adjacency: dict[str, list[tuple[str, float]]] = {node: [] for node in nodes}
        for edge in edges:
            a, b = str(edge["source"]), str(edge["target"])
            distance = float(edge["distance"])
            if a not in self.adjacency or b not in self.adjacency:
                raise ValueError(f"Edge references unknown node: {a!r} - {b!r}")
            if not isfinite(distance) or distance < 0:
                raise ValueError("edge distances must be finite and nonnegative")
            self.adjacency[a].append((b, distance))
            self.adjacency[b].append((a, distance))

    def dijkstra(self, start: str) -> tuple[dict[str, float], dict[str, str | None]]:
        if start not in self.adjacency:
            raise ValueError(f"Unknown start node: {start}")
        distances = {node: inf for node in self.nodes}
        previous: dict[str, str | None] = {node: None for node in self.nodes}
        distances[start] = 0.0
        queue = [(0.0, start)]
        while queue:
            distance, node = heappop(queue)
            if distance != distances[node]:
                continue
            for neighbor, weight in self.adjacency[node]:
                candidate = distance + weight
                if candidate < distances[neighbor]:
                    distances[neighbor] = candidate
                    previous[neighbor] = node
                    heappush(queue, (candidate, neighbor))
        return distances, previous

    @staticmethod
    def reconstruct_path(target: str, distances: dict[str, float], previous: dict[str, str | None]) -> tuple[str, ...]:
        if target not in distances or not isfinite(distances[target]):
            raise ValueError(f"Destination {target!r} is unreachable")
        path = [target]
        while previous[path[-1]] is not None:
            path.append(previous[path[-1]])
        path.reverse()
        return tuple(path)

    def shortest_path(self, start: str, target: str) -> tuple[float, tuple[str, ...]]:
        distances, previous = self.dijkstra(start)
        return distances[target], self.reconstruct_path(target, distances, previous)
