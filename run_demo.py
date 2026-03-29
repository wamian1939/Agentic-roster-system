"""
演示：完整排班流程
"""
import sys
import io
import json
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from data.models import Employee
from core.parser import build_availability_matrix
from core.env_utils import load_project_env
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
load_project_env(PROJECT_ROOT)

USE_ORTOOLS = False
if USE_ORTOOLS:
    from core.solver import solve_schedule
else:
    from core.solver_simple import solve_greedy


def load_weights_config(config_path: Path = None) -> dict:
    """从 config/weights_config.json 加载员工权重配置"""
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "weights_config.json"
    
    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
        weights = config.get("weights", {})
        print(f"✓ 从 {config_path} 加载了 {len(weights)} 名员工的权重配置")
        return weights
    except FileNotFoundError:
        print(f"⚠️  权重配置文件不存在: {config_path}")
        print("   使用默认权重（所有员工 0.5）")
        return {}

# 示例员工改为你提供的报班名单
employees = [
    Employee(id="Judy Zhu", level=2, max_hours_week=999),
    Employee(id="Jasmine Liu", level=2, max_hours_week=999),
    Employee(id="Viko Ge", level=2, max_hours_week=999),
    Employee(id="Zoe Wong", level=2, max_hours_week=999),
    Employee(id="Simeon Tian", level=2, max_hours_week=999),
    Employee(id="Kelly Lin", level=2, max_hours_week=999),
    Employee(id="Ou Liu", level=2, max_hours_week=999, is_full_position=True),
    Employee(id="Berlin", level=2, max_hours_week=999),
    Employee(id="Jenny Chen", level=2, max_hours_week=999),
    Employee(id="Tina Gu", level=2, max_hours_week=999, is_full_position=True),
    Employee(id="Winnie Wang", level=2, max_hours_week=999, is_full_position=True),
    Employee(id="Junbin Wu", level=2, max_hours_week=999),
    Employee(id="Maomao Wu", level=2, max_hours_week=999, is_full_position=True),
    Employee(id="Halsey", level=2, max_hours_week=999),
    Employee(id="Shelly Wang", level=2, max_hours_week=999),
    Employee(id="Jack Li", level=2, max_hours_week=999, is_full_position=True),
    Employee(id="Tomy", level=2, max_hours_week=999),
    Employee(id="Kelsey", level=2, max_hours_week=999),
]
# 报班代码：按 1234AA67BB 格式，数字=周几，AA/BB/CC=班次
availability_raw = {
    "Judy Zhu": "1CC3BB4CC",
    "Jasmine Liu": "14AA35CC",
    "Viko Ge": "4CC67BB",
    "Zoe Wong": "257BB",
    "Simeon Tian": "13567AA",
    "Kelly Lin": "34BB",
    "Ou Liu": "13567AA",
    "Berlin": "123467AA",
    "Jenny Chen": "124CC 67AA",
    "Tina Gu": "267AA5BB",
    "Winnie Wang": "2CC3AA5CC67AA",
    "Junbin Wu": "2367AA",
    "Maomao Wu": "23567AA",
    "Halsey": "1CC2BB5CC6CC7BB",
    "Shelly Wang": "23AA14BB",
    "Jack Li": "3467aa",
    "Tomy": "135cc67aa",
    "Kelsey": "23467AA5BB",
}

# ==========================================
# 从配置文件加载权重
# ==========================================
personal_weights = load_weights_config()


def build_demand(base_day_required: int, base_night_required: int):
    """按规则里的基础需求构造周需求，再叠加特殊日覆盖"""
    R = {}
    for d in range(1, 8):
        R[(d, "BB")] = int(base_day_required)
        R[(d, "CC")] = int(base_night_required)
        R[(d, "AA")] = 0
        R[(d, "LATE14")] = 0
    return R


def load_demo_policies(config_path: Path):
    """从 rules_hard.json 读取硬规则参数 + demo 的 meta 配置"""
    with open(config_path, encoding="utf-8") as f:
        rules = json.load(f)

    base_day_required = 0
    base_night_required = 0
    demand_overrides = []
    scheduling_policy = {}

    for rule in rules:
        c = rule.get("constraint", {})
        name = c.get("name")
        params = c.get("params", {})
        r_type = rule.get("type")

        if r_type == "hard" and name == "min_coverage_with_full_position":
            shifts = set(params.get("shifts", []))
            required = int(params.get("required", 0))
            min_full = int(params.get("min_full_position", 0))
            if "BB" in shifts:
                base_day_required = required
                scheduling_policy["day_min_full_position"] = min_full
            if "CC" in shifts:
                base_night_required = required
                scheduling_policy["night_min_full_position"] = min_full
        elif r_type == "hard" and name == "open_early_from_aa_bb":
            scheduling_policy["open_early_required"] = int(params.get("required", 3))
            scheduling_policy["open_early_min_full_position"] = int(params.get("min_full_position", 1))
        elif r_type == "meta" and name == "demo_special_day_demands":
            demand_overrides = params.get("overrides", [])
        elif r_type == "meta" and name in {
            "weekend_assign_policy",
            "aa_daily_policy",
            "combo_daily_policy",
        }:
            scheduling_policy.update(params)

    if base_day_required <= 0 or base_night_required <= 0:
        raise ValueError("rules_hard.json 缺少基础覆盖规则，请检查 H_DAY_COVERAGE / H_NIGHT_COVERAGE。")
    return base_day_required, base_night_required, demand_overrides, scheduling_policy


def apply_demand_overrides(R, overrides):
    for item in overrides:
        d = int(item.get("day"))
        if not (1 <= d <= 7):
            continue
        for k in ("BB", "CC", "AA", "LATE14"):
            if k in item:
                R[(d, k)] = int(item[k])


def print_schedule(schedule):
    """输出班表。AA覆盖10-22，故白天(11-17)=AA+BB，晚班(17-22)=AA+CC"""
    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    table = {}
    for s in schedule:
        d, sh, emp = s["day"], s["shift"], s["employee"]
        table.setdefault((d, sh), []).append(emp)

    print("\n" + "=" * 110)
    print("排班表（开早3人10:00；可设14:00补位；白天/晚班按每日需求）")
    print("=" * 110)
    print(f"{'日期':<6} {'AA全天(10-22)':<24} {'BB白天(11-17)':<24} {'CC晚班(17-22)':<24} {'白天合计':<12} {'晚班合计':<12}")
    print("-" * 110)
    for d in range(1, 8):
        aa = sorted(table.get((d, "AA"), []))
        bb = sorted(table.get((d, "BB"), []))
        cc = sorted(table.get((d, "CC"), []))
        day_total = aa + bb
        night_total = aa + cc
        aa_s = ", ".join(aa) or "-"
        bb_s = ", ".join(bb) or "-"
        cc_s = ", ".join(cc) or "-"
        open_early = ", ".join(
            sorted([s["employee"] for s in schedule if s["day"] == d and s["shift"] == "BB" and s.get("start_hour") == 10])
        ) or "-"
        late_arrive = ", ".join(
            sorted([s["employee"] for s in schedule if s["day"] == d and s.get("start_hour") == 14])
        ) or "-"
        print(
            f"{day_names[d-1]:<6} {aa_s:<24} {bb_s:<24} {cc_s:<24} "
            f"{len(day_total)}人{'':<6} {len(night_total)}人  开早:{open_early}  两点:{late_arrive}"
        )
    print("=" * 110)
    print(f"共 {len(schedule)} 个班次")


A = build_availability_matrix(employees, availability_raw)
(
    base_day_required,
    base_night_required,
    overrides,
    scheduling_policy,
) = load_demo_policies(Path(__file__).parent / "config" / "rules_hard.json")
R = build_demand(base_day_required, base_night_required)
apply_demand_overrides(R, overrides)

if USE_ORTOOLS:
    schedule, status = solve_schedule(A, R, employees)
    schedule = schedule or []
else:
    schedule = solve_greedy(
        A,
        R,
        employees,
        personal_weights=personal_weights,
        scheduling_policy=scheduling_policy,
    )

if schedule:
    print_schedule(schedule)
    # 生成图形化 HTML 班表
    from core.visualize import schedule_to_html
    rule_suggestions = None
    html_path = Path(__file__).parent / "output" / "schedule.html"
    if os.getenv("ENABLE_AI_DIAGNOSIS", "0") == "1":
        from core.diagnosis_agent import diagnose_schedule_with_chatgpt
        from core.agents.common import build_schedule_summary, load_rules
        from core.agents.risk_agent import run_risk_agent
        from core.agents.weight_agent import run_weight_agent
        from core.agents.rule_suggestion_agent import run_rule_suggestion_agent
        try:
            rules_path = Path(__file__).parent / "config" / "rules_hard.json"
            diagnosis = diagnose_schedule_with_chatgpt(
                schedule=schedule,
                employees=employees,
                rules_path=rules_path,
                personal_weights=personal_weights,
            )
            diag_path = Path(__file__).parent / "output" / "diagnosis.md"
            diag_path.write_text(diagnosis, encoding="utf-8")
            print(f"AI诊断报告已生成: {diag_path.absolute()}")

            # 规则建议 Agent（结构化 JSON）
            summary = build_schedule_summary(schedule, employees)
            rules = load_rules(rules_path)
            weight_result = run_weight_agent(summary, personal_weights, employees)
            risk_result = run_risk_agent(schedule, summary, rules)
            rule_suggestions = run_rule_suggestion_agent(rules, summary, weight_result, risk_result)
            sugg_path = Path(__file__).parent / "output" / "rule_suggestions.json"
            sugg_path.write_text(json.dumps(rule_suggestions, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"规则建议已生成: {sugg_path.absolute()}")

            # 可选：让 Agent 自动把建议写回规则文件（默认关闭）
            if os.getenv("ENABLE_AI_RULE_AUTO_APPLY", "0") == "1":
                from core.agents.rule_apply_agent import apply_and_save_rules
                overwrite = os.getenv("ENABLE_AI_RULE_OVERWRITE", "0") == "1"
                apply_result = apply_and_save_rules(
                    rules_path=rules_path,
                    suggestions=rule_suggestions.get("suggestions", []),
                    overwrite=overwrite,
                )
                print(
                    f"规则自动应用完成: {apply_result['applied_count']} 条 -> "
                    f"{apply_result['output_path']}"
                )
        except Exception as e:
            print(f"AI诊断失败: {e}")
    schedule_to_html(schedule, html_path, rule_suggestions=rule_suggestions)
    print(f"\n图形化班表已生成: {html_path.absolute()}")
    print("如需网页内一键 Apply 建议并重排，请先运行: python integration/demo_apply_server.py")
else:
    print("无可行解")
