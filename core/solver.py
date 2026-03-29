"""
排班求解器：CP-SAT 约束优化 + 规则引擎
"""
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from ortools.sat.python import cp_model
from core.rules import register, load_rules, build_constraints_from_rules


@register("only_assign_if_available")
def build_availability_constraint(model, x, context, params):
    """硬约束：只能在可用时段排班。x[e,d,s]=1 时必须有 A[e,d,s]=1"""
    A = context["A"]
    for (e, d, s), avail in A.items():
        if avail == 0:
            var_key = (e, d, s)
            if var_key in x:
                model.Add(x[var_key] == 0)


@register("min_coverage")
def build_coverage_constraint(model, x, context, params):
    """硬约束：每个 (day, shift) 至少需要 R[d,s] 人"""
    R = context["R"]
    employees = context["employees"]
    for (d, s), req in R.items():
        assigned = [
            x[(e.id, d, s)]
            for e in employees
            if (e.id, d, s) in x
        ]
        if assigned:
            model.Add(sum(assigned) >= req)


@register("max_week_hours")
def build_week_hours_constraint(model, x, context, params):
    """硬约束：员工周工时不超过上限"""
    shift_hours = params.get("shift_hours", {"AA": 12, "CC": 7, "BB": 5})
    employees = context["employees"]
    for e in employees:
        terms = [
            var * shift_hours.get(s, 0)
            for (emp_id, d, s), var in x.items()
            if emp_id == e.id
        ]
        if terms:
            model.Add(sum(terms) <= e.max_hours_week)


def solve_schedule(A, R, employees, rules_dir: Path = None):
    """
    主求解流程：建模型 → 加约束 → 求解 → 返回班表
    A: 可用性矩阵 {(e,d,s): 0|1}
    R: 需求 {(d,s): required_count}
    """
    rules_dir = rules_dir or Path(__file__).parent.parent / "config"
    model = cp_model.CpModel()
    x = {}
    for (e, d, s), avail in A.items():
        if avail == 1:
            x[(e, d, s)] = model.NewBoolVar(f"x_{e}_{d}_{s}")

    context = {"A": A, "R": R, "employees": employees}
    hard_rules = load_rules(rules_dir / "rules_hard.json")
    build_constraints_from_rules(hard_rules, model, x, context)

    model.Minimize(0)  # 先求可行解
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status != cp_model.OPTIMAL and status != cp_model.FEASIBLE:
        return None, status

    schedule = []
    for (e, d, s), var in x.items():
        if solver.Value(var) == 1:
            schedule.append({"employee": e, "day": d, "shift": s})
    return schedule, status
