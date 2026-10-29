"""Orchestrates ranking, capacity selection, shortest paths and delivery routing."""
from time import perf_counter
from .graph import RoadGraph
from .knapsack import select_parcels
from .models import Parcel, PlanResult
from .routing import nearest_neighbor_route
from .sorting import merge_sort_parcels


def create_plan(parcels: list[Parcel], graph: RoadGraph, depot: str, capacity: int) -> PlanResult:
    timings: dict[str, float] = {}
    start = perf_counter(); ranked = merge_sort_parcels(parcels)
    timings["sorting"] = (perf_counter() - start) * 1000
    start = perf_counter(); chosen, used, _dp = select_parcels(ranked, capacity)
    timings["knapsack"] = (perf_counter() - start) * 1000
    destinations = sorted({p.destination for p in chosen})
    start = perf_counter()
    depot_distances, depot_previous = graph.dijkstra(depot)
    shortest: dict[str, tuple[float, tuple[str, ...]]] = {}
    for destination in destinations:
        if destination not in depot_distances:
            raise ValueError(f"Unknown destination: {destination}")
        shortest[destination] = (depot_distances[destination], graph.reconstruct_path(destination, depot_distances, depot_previous))
    timings["dijkstra"] = (perf_counter() - start) * 1000
    start = perf_counter(); order, expanded, total = nearest_neighbor_route(graph, depot, destinations, shortest)
    timings["route_planning"] = (perf_counter() - start) * 1000
    return PlanResult(tuple(ranked), tuple(chosen), used, capacity, order, expanded, total, shortest, timings)
