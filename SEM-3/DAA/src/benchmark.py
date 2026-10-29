"""Deterministic multi-size runtime experiment and optional PNG chart."""
import argparse
import csv
import random
import time
from pathlib import Path
from statistics import median
from .graph import RoadGraph
from .models import Parcel
from .planner import create_plan
from .sorting import merge_sort_parcels
from .knapsack import select_parcels


def make_case(size: int, seed: int = 1729):
    rng = random.Random(seed + size)
    nodes = ["DEPOT"] + [f"N{i:03d}" for i in range(size)]
    edges = []
    for i in range(len(nodes) - 1):
        edges.append({"source": nodes[i], "target": nodes[i + 1], "distance": rng.randint(1, 20)})
    # Add deterministic random shortcuts while retaining a connected backbone.
    for _ in range(size * 2):
        i, j = sorted(rng.sample(range(len(nodes)), 2))
        edges.append({"source": nodes[i], "target": nodes[j], "distance": rng.randint(1, 25)})
    graph = RoadGraph(nodes, edges)
    parcels = [Parcel(f"P{i:04d}", nodes[i + 1], rng.randint(1, 12),
                      f"2026-11-{1 + i % 28:02d}T{8 + i % 10:02d}:00", rng.randint(1, 20))
               for i in range(size)]
    return parcels, graph, "DEPOT", max(1, size * 5)


def measure(function, repeats: int = 5) -> float:
    observations = []
    for _ in range(repeats):
        start = time.perf_counter(); function(); observations.append((time.perf_counter() - start) * 1000)
    return median(observations)


def run_benchmarks(sizes=(20, 50, 100, 200)) -> list[dict]:
    rows = []
    for size in sizes:
        parcels, graph, depot, capacity = make_case(size)
        ranked = merge_sort_parcels(parcels)
        cases = {
            "sorting": lambda: merge_sort_parcels(parcels),
            "knapsack": lambda: select_parcels(ranked, capacity),
            "dijkstra": lambda: graph.dijkstra(depot),
            "route_planning": lambda: create_plan(parcels, graph, depot, capacity),
        }
        for component, function in cases.items():
            rows.append({"size": size, "component": component, "median_ms": measure(function)})
    return rows


def write_csv(rows: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["size", "component", "median_ms"])
        writer.writeheader(); writer.writerows(rows)


def write_chart(rows: list[dict], output: Path) -> bool:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    output.parent.mkdir(parents=True, exist_ok=True)
    components = sorted({row["component"] for row in rows})
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for component in components:
        data = [row for row in rows if row["component"] == component]
        ax.plot([r["size"] for r in data], [r["median_ms"] for r in data], marker="o", linewidth=2, label=component)
    ax.set(title="Mini-Courier Planner: median runtime by input size", xlabel="Parcel count / destination nodes", ylabel="Median elapsed time (ms)")
    ax.grid(True, alpha=.25); ax.legend(); fig.tight_layout(); fig.savefig(output, dpi=170); plt.close(fig)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("images/runtime_benchmarks.png"))
    parser.add_argument("--csv", type=Path, default=Path("results/benchmark_results.csv"))
    args = parser.parse_args()
    rows = run_benchmarks(); write_csv(rows, args.csv)
    plotted = write_chart(rows, args.output)
    print("size component median_ms")
    for row in rows:
        print(f"{row['size']:>4} {row['component']:<16} {row['median_ms']:.4f}")
    print(f"CSV: {args.csv}")
    print(f"Chart: {args.output}" if plotted else "Chart skipped: install matplotlib to generate PNG.")


if __name__ == "__main__":
    main()
