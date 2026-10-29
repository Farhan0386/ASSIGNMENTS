"""Typed data models and input validation for the courier planner."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Parcel:
    parcel_id: str
    destination: str
    weight: int
    deadline: str
    priority: int

    @classmethod
    def from_dict(cls, row: dict) -> "Parcel":
        required = {"parcel_id", "destination", "weight", "deadline", "priority"}
        missing = required - row.keys()
        if missing:
            raise ValueError(f"Parcel is missing fields: {sorted(missing)}")
        parcel = cls(str(row["parcel_id"]), str(row["destination"]), int(row["weight"]),
                     str(row["deadline"]), int(row["priority"]))
        if not parcel.parcel_id or not parcel.destination:
            raise ValueError("parcel_id and destination must not be empty")
        if parcel.weight <= 0:
            raise ValueError(f"Parcel {parcel.parcel_id} weight must be positive")
        if parcel.priority < 0:
            raise ValueError(f"Parcel {parcel.parcel_id} priority must be nonnegative")
        return parcel


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    distance: float


@dataclass(frozen=True)
class PlanResult:
    ranked_parcels: tuple[Parcel, ...]
    selected_parcels: tuple[Parcel, ...]
    used_capacity: int
    capacity: int
    stop_order: tuple[str, ...]
    expanded_route: tuple[str, ...]
    total_distance: float
    shortest_paths: dict[str, tuple[float, tuple[str, ...]]]
    timings_ms: dict[str, float]
