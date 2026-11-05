"""Deterministic unit and end-to-end checks for the planning pipeline."""
import unittest
from pathlib import Path
from src.graph import RoadGraph
from src.io_utils import load_inputs
from src.knapsack import select_parcels
from src.models import Parcel
from src.planner import create_plan
from src.routing import nearest_neighbor_route
from src.sorting import merge_sort_parcels


class SortingTests(unittest.TestCase):
    def test_priority_deadline_and_id_order(self):
        parcels = [Parcel("z", "A", 1, "2026-01-02", 5), Parcel("b", "A", 1, "2026-01-01", 5),
                   Parcel("a", "A", 1, "2026-01-01", 5), Parcel("x", "A", 1, "2025-01-01", 8)]
        self.assertEqual([p.parcel_id for p in merge_sort_parcels(parcels)], ["x", "a", "b", "z"])
        self.assertEqual(len(parcels), 4)  # input is not mutated


class KnapsackTests(unittest.TestCase):
    def test_capacity_and_optimal_priority(self):
        items = [Parcel("a", "A", 4, "d", 8), Parcel("b", "B", 7, "d", 12),
                 Parcel("c", "C", 5, "d", 10), Parcel("d", "D", 6, "d", 9)]
        chosen, used, table = select_parcels(items, 11)
        self.assertEqual(sum(p.priority for p in chosen), 20)
        self.assertEqual(used, 11)
        self.assertLessEqual(used, 11)
        self.assertEqual(table[-1][-1], 20)

    def test_negative_capacity_rejected(self):
        with self.assertRaises(ValueError):
            select_parcels([], -1)


class GraphTests(unittest.TestCase):
    def test_dijkstra_uses_indirect_shorter_path(self):
        graph = RoadGraph(["S", "A", "T"], [{"source": "S", "target": "T", "distance": 9},
                          {"source": "S", "target": "A", "distance": 2}, {"source": "A", "target": "T", "distance": 3}])
        distance, path = graph.shortest_path("S", "T")
        self.assertEqual(distance, 5)
        self.assertEqual(path, ("S", "A", "T"))

    def test_unreachable_path_is_clear(self):
        graph = RoadGraph(["S", "T"], [])
        with self.assertRaisesRegex(ValueError, "unreachable"):
            graph.shortest_path("S", "T")


class IntegrationTests(unittest.TestCase):
    def test_sample_pipeline_is_feasible_and_closed(self):
        root = Path(__file__).resolve().parents[1]
        parcels, graph, depot, capacity = load_inputs(root / "datasets")
        plan = create_plan(parcels, graph, depot, capacity)
        self.assertLessEqual(plan.used_capacity, capacity)
        self.assertEqual(plan.stop_order[0], depot)
        self.assertEqual(plan.stop_order[-1], depot)
        self.assertAlmostEqual(plan.total_distance, 22.0)
        self.assertEqual(set(plan.stop_order[1:-1]), {"B", "C", "E"})

    def test_empty_batch_is_zero_length_tour(self):
        graph = RoadGraph(["D", "A"], [{"source": "D", "target": "A", "distance": 1}])
        order, route, distance = nearest_neighbor_route(graph, "D", [])
        self.assertEqual(order, ("D",))
        self.assertEqual(route, ("D",))
        self.assertEqual(distance, 0)


if __name__ == "__main__":
    unittest.main()
