from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class Candidate:
    sku_id: str
    moq: int
    max_units: int
    unit_cost: float
    unit_margin: float
    shortage_units: float
    stockout_risk: float


def allocate_budget(candidates: list[Candidate], budget: float, max_states: int = 20_000) -> dict[str, int]:
    """Deterministic bounded knapsack over MOQ-sized purchase bundles.

    Costs are rounded upward to an adaptive integer unit, so the selected plan
    can never exceed the real budget. Utility represents protected margin,
    weighted by forecast shortage risk.
    """
    if budget <= 0 or not candidates:
        return {candidate.sku_id: 0 for candidate in candidates}

    scale = max(1, ceil(budget / max_states))
    capacity = int(budget // scale)
    bundles: list[tuple[str, int, int, float]] = []
    for candidate in sorted(candidates, key=lambda item: item.sku_id):
        bundle_cost = candidate.moq * candidate.unit_cost
        scaled_cost = max(1, ceil(bundle_cost / scale))
        count = candidate.max_units // candidate.moq
        for bundle_index in range(count):
            remaining_shortage = max(0.0, candidate.shortage_units - bundle_index * candidate.moq)
            protected_units = min(float(candidate.moq), remaining_shortage)
            utility = protected_units * max(candidate.unit_margin, 0.01) * max(candidate.stockout_risk, 0.01)
            bundles.append((candidate.sku_id, candidate.moq, scaled_cost, utility))

    values = [-1.0] * (capacity + 1)
    picks: list[tuple[int, int] | None] = [None] * (capacity + 1)
    values[0] = 0.0
    for bundle_index, (_, _, cost, utility) in enumerate(bundles):
        for current in range(capacity, cost - 1, -1):
            previous = current - cost
            if values[previous] < 0:
                continue
            proposed = values[previous] + utility
            if proposed > values[current] + 1e-12:
                values[current] = proposed
                picks[current] = (previous, bundle_index)

    best_cost = max(range(capacity + 1), key=lambda index: (values[index], -index))
    allocation = {candidate.sku_id: 0 for candidate in candidates}
    cursor = best_cost
    while cursor > 0 and picks[cursor] is not None:
        previous, bundle_index = picks[cursor]
        sku_id, units, _, _ = bundles[bundle_index]
        allocation[sku_id] += units
        cursor = previous

    actual_cost = sum(
        allocation[candidate.sku_id] * candidate.unit_cost for candidate in candidates
    )
    if actual_cost > budget + 1e-6:
        raise RuntimeError("Budget optimizer produced an infeasible allocation.")
    return allocation

