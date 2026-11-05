"""Stable merge sort for the parcel-priority policy."""
from .models import Parcel


def parcel_sort_key(parcel: Parcel) -> tuple:
    # Larger priority first, then earlier ISO-8601 deadline, then ID for reproducibility.
    return (-parcel.priority, parcel.deadline, parcel.parcel_id)


def merge_sort_parcels(parcels: list[Parcel]) -> list[Parcel]:
    """Return a stable O(n log n) ordering without changing the input list."""
    if len(parcels) < 2:
        return list(parcels)
    middle = len(parcels) // 2
    left = merge_sort_parcels(parcels[:middle])
    right = merge_sort_parcels(parcels[middle:])
    merged: list[Parcel] = []
    i = j = 0
    while i < len(left) and j < len(right):
        if parcel_sort_key(left[i]) <= parcel_sort_key(right[j]):
            merged.append(left[i]); i += 1
        else:
            merged.append(right[j]); j += 1
    merged.extend(left[i:]); merged.extend(right[j:])
    return merged
