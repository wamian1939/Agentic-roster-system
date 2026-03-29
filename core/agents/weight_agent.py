"""
权重诊断 Agent：专注权重与实际排班偏差
"""
from typing import Dict


def _normalize_weights(personal_weights: Dict[str, float], employees: list) -> Dict[str, float]:
    result = {}
    for e in employees:
        w = float(personal_weights.get(e.id, 0.5))
        result[e.id] = max(0.0, min(1.0, w))
    return result


def run_weight_agent(summary: Dict, personal_weights: Dict[str, float], employees: list) -> Dict:
    by_employee = summary["by_employee"]
    actual_totals = {eid: int(v.get("total", 0)) for eid, v in by_employee.items()}
    total_assignments = sum(actual_totals.values())

    normalized_weights = _normalize_weights(personal_weights, employees)
    weight_sum = sum(normalized_weights.values()) or 1.0

    items = []
    for eid in by_employee.keys():
        expected = (normalized_weights[eid] / weight_sum) * total_assignments
        actual = actual_totals[eid]
        gap = round(actual - expected, 2)
        items.append(
            {
                "employee": eid,
                "weight": round(normalized_weights[eid], 3),
                "expected_total": round(expected, 2),
                "actual_total": actual,
                "gap_actual_minus_expected": gap,
            }
        )

    over_assigned = sorted(items, key=lambda x: x["gap_actual_minus_expected"], reverse=True)[:5]
    under_assigned = sorted(items, key=lambda x: x["gap_actual_minus_expected"])[:5]

    return {
        "total_assignments": total_assignments,
        "weight_sum": round(weight_sum, 3),
        "top_over_assigned": over_assigned,
        "top_under_assigned": under_assigned,
        "all": items,
    }
