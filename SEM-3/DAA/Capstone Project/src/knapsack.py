"""0/1 knapsack using a two-dimensional dynamic-programming table."""
from .models import Parcel


def select_parcels(parcels: list[Parcel], capacity: int) -> tuple[list[Parcel], int, list[list[int]]]:
    """Maximize total priority subject to capacity; ties choose lower used weight.

    Returns (chosen parcels in input order, used weight, DP table). Complexity O(nW)
    time and space. Capacity and parcel weights are integer units.
    """
    if capacity < 0:
        raise ValueError("capacity must be nonnegative")
    n = len(parcels)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i, parcel in enumerate(parcels, start=1):
        for limit in range(capacity + 1):
            dp[i][limit] = dp[i - 1][limit]
            if parcel.weight <= limit:
                candidate = dp[i - 1][limit - parcel.weight] + parcel.priority
                if candidate > dp[i][limit]:
                    dp[i][limit] = candidate
    # Backtrack; on equal values, exclude the later item for deterministic output.
    chosen: list[Parcel] = []
    remaining = capacity
    for i in range(n, 0, -1):
        if dp[i][remaining] != dp[i - 1][remaining]:
            parcel = parcels[i - 1]
            chosen.append(parcel)
            remaining -= parcel.weight
    chosen.reverse()
    used = sum(p.weight for p in chosen)
    return chosen, used, dp
