"""Command-line entry point for the Mini-Courier Planner."""
from pathlib import Path
from .io_utils import load_inputs
from .planner import create_plan


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parcels, graph, depot, capacity = load_inputs(root / "datasets")
    result = create_plan(parcels, graph, depot, capacity)
    print("MINI-COURIER PLANNER")
    print(f"Depot: {depot} | Vehicle capacity: {capacity} weight units")
    print("\nParcel ranking (priority desc, deadline asc):")
    for index, parcel in enumerate(result.ranked_parcels, 1):
        print(f"  {index}. {parcel.parcel_id}: priority={parcel.priority}, deadline={parcel.deadline}, weight={parcel.weight}, destination={parcel.destination}")
    print("\nSelected delivery batch (0/1 knapsack):")
    for parcel in result.selected_parcels:
        print(f"  {parcel.parcel_id} -> {parcel.destination} ({parcel.weight} units, priority {parcel.priority})")
    print(f"Capacity used: {result.used_capacity}/{result.capacity} | total priority: {sum(p.priority for p in result.selected_parcels)}")
    print("\nShortest paths from depot:")
    for destination, (distance, path) in sorted(result.shortest_paths.items()):
        print(f"  {depot} -> {destination}: {' -> '.join(path)} ({distance:g} km)")
    print("\nNearest-neighbor delivery tour:")
    print(f"  Stops: {' -> '.join(result.stop_order)}")
    print(f"  Road path: {' -> '.join(result.expanded_route)}")
    print(f"  Total distance (including return to depot): {result.total_distance:g} km")
    print("\nComponent runtime (single illustrative run; hardware-dependent):")
    for stage, elapsed in result.timings_ms.items():
        print(f"  {stage}: {elapsed:.4f} ms")


if __name__ == "__main__":
    main()
