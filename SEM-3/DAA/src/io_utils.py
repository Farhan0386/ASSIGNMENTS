"""JSON loading helpers."""
import json
from pathlib import Path
from .graph import RoadGraph
from .models import Parcel


def load_inputs(data_dir: Path) -> tuple[list[Parcel], RoadGraph, str, int]:
    parcel_data = json.loads((data_dir / "parcels.json").read_text(encoding="utf-8"))
    route_data = json.loads((data_dir / "road_network.json").read_text(encoding="utf-8"))
    parcels = [Parcel.from_dict(row) for row in parcel_data["parcels"]]
    if len({p.parcel_id for p in parcels}) != len(parcels):
        raise ValueError("parcel IDs must be unique")
    graph = RoadGraph(route_data["nodes"], route_data["edges"])
    for parcel in parcels:
        if parcel.destination not in graph.adjacency:
            raise ValueError(f"Parcel {parcel.parcel_id} references unknown destination {parcel.destination}")
    depot = str(route_data["depot"])
    capacity = int(parcel_data["vehicle_capacity"])
    if capacity < 0:
        raise ValueError("vehicle_capacity must be nonnegative")
    return parcels, graph, depot, capacity
