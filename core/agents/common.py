"""
多 Agent 共享工具：排班摘要与规则读取
"""
import json
from pathlib import Path
from typing import Dict, List


def build_schedule_summary(schedule: List[Dict], employees: list) -> Dict:
    emp_ids = [e.id for e in employees]
    by_emp = {eid: {"AA": 0, "BB": 0, "CC": 0, "total": 0} for eid in emp_ids}
    by_day = {d: {"AA": 0, "BB": 0, "CC": 0, "late14": 0} for d in range(1, 8)}
    for s in schedule:
        eid = s["employee"]
        sh = s["shift"]
        d = int(s["day"])
        if eid in by_emp and sh in by_emp[eid]:
            by_emp[eid][sh] += 1
            by_emp[eid]["total"] += 1
        if sh in by_day[d]:
            by_day[d][sh] += 1
        if s.get("start_hour") == 14:
            by_day[d]["late14"] += 1
    totals = [v["total"] for v in by_emp.values()]
    fairness = {
        "min_total": min(totals) if totals else 0,
        "max_total": max(totals) if totals else 0,
        "avg_total": round(sum(totals) / len(totals), 2) if totals else 0.0,
    }
    return {"by_employee": by_emp, "by_day": by_day, "fairness": fairness}


def load_rules(rules_path: Path) -> List[Dict]:
    with open(rules_path, encoding="utf-8") as f:
        return json.load(f)
