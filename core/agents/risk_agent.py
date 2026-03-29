"""
排班风险 Agent：专注规则执行和结构风险
"""
from typing import Dict, List


def _meta_params(rules: List[Dict], name: str) -> Dict:
    for r in rules:
        if r.get("type") == "meta" and r.get("constraint", {}).get("name") == name:
            return r.get("constraint", {}).get("params", {})
    return {}


def run_risk_agent(schedule: List[Dict], summary: Dict, rules: List[Dict]) -> Dict:
    by_day = summary["by_day"]

    combo_by_day = {}
    for d in range(1, 8):
        bb = {s["employee"] for s in schedule if s["day"] == d and s["shift"] == "BB"}
        cc = {s["employee"] for s in schedule if s["day"] == d and s["shift"] == "CC"}
        combo_by_day[d] = len(bb & cc)

    combo_pref = int(_meta_params(rules, "combo_daily_policy").get("max_bb_cc_combo_per_day_preferred", 2))
    late_rules = {
        int(x.get("day")): int(x.get("LATE14", 0))
        for x in _meta_params(rules, "demo_special_day_demands").get("overrides", [])
        if x.get("day") is not None
    }
    late_actual = {d: int(by_day[d].get("late14", 0)) for d in range(1, 8)}

    risk_items = []
    for d in range(1, 8):
        if combo_by_day[d] > combo_pref:
            risk_items.append({"day": d, "type": "combo_exceed", "value": combo_by_day[d], "limit": combo_pref})
        required_late = late_rules.get(d, 0)
        if required_late != late_actual[d]:
            risk_items.append(
                {"day": d, "type": "late14_mismatch", "required": required_late, "actual": late_actual[d]}
            )

    return {
        "combo_by_day": combo_by_day,
        "combo_preferred_limit": combo_pref,
        "late14_required_by_day": late_rules,
        "late14_actual_by_day": late_actual,
        "risks": risk_items,
    }
