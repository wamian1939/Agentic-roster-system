"""
简化版排班求解器
开早(10-11)需3人，从AA或BB中选（报AA/BB的都可开早）。白天5人、晚班6人。任一时段≥1全岗。
"""
from itertools import combinations
from typing import Dict, List, Optional, Tuple
from data.models import SHIFT_HOURS


def _build_priority_score(
    A: Dict[Tuple[str, int, str], int],
    employee_ids: List[str],
    full_pos: Dict[str, bool],
    personal_weights: Dict[str, float],
) -> Dict[str, float]:
    """
    两段式权重：
    1) 初始个人权重：由外部手工设置（0~1）
    2) 自动算法加成：报班越多加成越高（固定算法，不暴露手调）
    3) 全岗加成：固定更高优先级，保证全岗权重层级最高
    """
    report_bonus_cap = 0.1   # 自动算法常量（内部固定）
    full_position_bonus = 0.5  # 自动算法常量（内部固定）

    reported_slots = {
        eid: sum(A.get((eid, d, s), 0) for d in range(1, 8) for s in ("AA", "BB", "CC"))
        for eid in employee_ids
    }
    max_reported = max(reported_slots.values()) if reported_slots else 0

    scores: Dict[str, float] = {}
    for eid in employee_ids:
        base = float(personal_weights.get(eid, 0.5))
        base = max(0.0, min(1.0, base))
        report_bonus = (reported_slots[eid] / max_reported) * report_bonus_cap if max_reported > 0 else 0.0
        full_bonus = full_position_bonus if full_pos.get(eid, False) else 0.0
        scores[eid] = base + report_bonus + full_bonus
    return scores


def solve_greedy(
    A: Dict[Tuple[str, int, str], int],
    R: Dict[Tuple[int, str], int],
    employees: list,
    personal_weights: Optional[Dict[str, float]] = None,
    scheduling_policy: Optional[Dict[str, object]] = None,
) -> List[Dict]:
    """
    约束优先的逐日求解：
    - 白天(11-17): BB = 5（其中3人开早10-17）
    - 晚班(17-22): AA + CC = 6
    - 开早(10-11): 从 BB 中选 3 人
    - 白天/晚班均至少 1 名全岗
    说明：报 AA 视为可排 BB/CC（不强制排AA），确保“只有3人10点上班”。
    """
    hours_used = {e.id: 0 for e in employees}
    max_hours = {e.id: e.max_hours_week for e in employees}
    full_pos = {e.id: e.is_full_position for e in employees}
    emp_level = {e.id: e.level for e in employees}
    employee_ids = [e.id for e in employees]
    schedule = []
    personal_weights = personal_weights or {}
    scheduling_policy = scheduling_policy or {}
    weekend_extra_allowed = str(scheduling_policy.get("extra_allowed_employee", "Winnie Wang"))
    prefer_even_distribution = bool(scheduling_policy.get("prefer_even_distribution", True))
    open_early_required = int(scheduling_policy.get("open_early_required", 3))
    open_early_min_full_position = int(scheduling_policy.get("open_early_min_full_position", 1))
    day_min_full_position = int(scheduling_policy.get("day_min_full_position", 1))
    night_min_full_position = int(scheduling_policy.get("night_min_full_position", 1))
    max_aa_per_day_preferred = int(scheduling_policy.get("max_aa_per_day_preferred", 2))
    relax_aa_if_infeasible = bool(scheduling_policy.get("relax_if_infeasible", True))
    max_combo_per_day_preferred = int(scheduling_policy.get("max_bb_cc_combo_per_day_preferred", 2))
    relax_combo_if_infeasible = bool(scheduling_policy.get("relax_if_infeasible", True))
    weekend_assigned = {e.id: 0 for e in employees}
    assigned_shift_count = {e.id: 0 for e in employees}
    assigned_day_count = {e.id: 0 for e in employees}
    aa_assigned_count = {e.id: 0 for e in employees}

    # 仅 personal_weights 由外部手工传入；其它加成由固定算法自动计算
    priority_score = _build_priority_score(A, employee_ids, full_pos, personal_weights)

    def rank_key(emp_id: str, d: int, shift: str):
        # 公平优先：先照顾“本周还没上过/上得少”的员工，再看权重
        unassigned_rank = 0 if assigned_shift_count[emp_id] == 0 else 1
        common = (
            unassigned_rank,
            assigned_day_count[emp_id],
            assigned_shift_count[emp_id],
        )
        if d in (6, 7) and prefer_even_distribution:
            weekend_rank = -1 if emp_id == weekend_extra_allowed else weekend_assigned[emp_id]
            common = (weekend_rank,) + common
        # 对 AA 增加抑制，避免全天班过于集中
        aa_rank = aa_assigned_count[emp_id] if shift == "AA" else 0
        return common + (aa_rank, -priority_score[emp_id], hours_used[emp_id], emp_id)

    def can_take(emp_id: str, d: int, shift: str) -> bool:
        avail = A.get((emp_id, d, shift), 0) == 1
        # 报 AA 的员工可被分配到 BB/CC（全天可拆分）
        if shift in ("BB", "CC"):
            avail = avail or (A.get((emp_id, d, "AA"), 0) == 1)
        return (
            avail
            and hours_used[emp_id] + SHIFT_HOURS.get(shift, 0) <= max_hours[emp_id]
        )

    for d in range(1, 8):
        day_need = R.get((d, "BB"), 5)
        night_need = R.get((d, "CC"), 6)
        late14_need = R.get((d, "LATE14"), 0)
        aa_candidates = sorted(
            [eid for eid in employee_ids if can_take(eid, d, "AA")],
            key=lambda x: rank_key(x, d, "AA"),
        )

        solved = False
        # AA 规则：优先尝试每天不超过上限；若无解再自动放宽
        max_a = min(day_need, night_need, len(aa_candidates))
        preferred_max = max(0, min(max_aa_per_day_preferred, max_a))
        aa_try_values = list(range(0, preferred_max + 1))
        if relax_aa_if_infeasible and preferred_max < max_a:
            aa_try_values.extend(range(preferred_max + 1, max_a + 1))

        for a in aa_try_values:
            b = day_need - a
            c = night_need - a
            if b < 0 or c < 0:
                continue
            aa_set = set(aa_candidates[:a])

            bb_candidates = sorted(
                [eid for eid in employee_ids if eid not in aa_set and can_take(eid, d, "BB")],
                key=lambda x: rank_key(x, d, "BB"),
            )
            cc_candidates = sorted(
                [eid for eid in employee_ids if eid not in aa_set and can_take(eid, d, "CC")],
                key=lambda x: rank_key(x, d, "CC"),
            )
            if len(bb_candidates) < b or len(cc_candidates) < c:
                continue

            # 允许 BB+CC 连班（11-17 接 17-22）；AA 不与其它班并存
            for bb_tuple in combinations(bb_candidates, b):
                bb_set = set(bb_tuple)

                # 周末优先减少 BB/CC 重叠，尽量让更多报班员工有班可上
                if d in (6, 7):
                    cc_pool = sorted(
                        cc_candidates,
                        key=lambda x: (
                            1 if (x in bb_set and x != weekend_extra_allowed) else 0,
                            *rank_key(x, d, "CC"),
                        ),
                    )
                else:
                    cc_pool = cc_candidates
                if len(cc_pool) < c:
                    continue
                cc_only_pool = [eid for eid in cc_pool if eid not in bb_set]
                cc_overlap_pool = [eid for eid in cc_pool if eid in bb_set]
                min_overlap_needed = max(0, c - len(cc_only_pool))
                max_overlap_possible = min(c, len(cc_overlap_pool))
                combo_pref = max(0, min(max_combo_per_day_preferred, max_overlap_possible))
                overlap_values = [
                    ov for ov in range(min_overlap_needed, max_overlap_possible + 1) if ov <= combo_pref
                ]
                if relax_combo_if_infeasible and not overlap_values:
                    overlap_values = list(range(min_overlap_needed, max_overlap_possible + 1))
                if not overlap_values:
                    continue

                cc_set = set()
                for overlap_cnt in overlap_values:
                    cc_only_needed = c - overlap_cnt
                    if cc_only_needed < 0 or cc_only_needed > len(cc_only_pool):
                        continue
                    cc_pick = cc_only_pool[:cc_only_needed] + cc_overlap_pool[:overlap_cnt]
                    if len(cc_pick) == c:
                        cc_set = set(cc_pick)
                        break
                if not cc_set:
                    continue

                day_staff = aa_set | bb_set
                night_staff = aa_set | cc_set
                all_staff = aa_set | bb_set | cc_set
                if len(day_staff) < day_need or len(night_staff) < night_need:
                    continue
                day_full_count = sum(1 for eid in day_staff if full_pos.get(eid, False))
                night_full_count = sum(1 for eid in night_staff if full_pos.get(eid, False))
                if day_full_count < day_min_full_position:
                    continue
                if night_full_count < night_min_full_position:
                    continue
                if not any(emp_level.get(eid, 0) >= 2 for eid in all_staff):
                    continue
                if len(bb_set) < open_early_required:
                    continue

                # 从BB中选开早人数，且满足最少全岗人数
                bb_sorted = sorted(bb_set, key=lambda x: rank_key(x, d, "BB"))
                open_early = set(bb_sorted[:open_early_required])
                open_early_full_count = sum(1 for eid in open_early if full_pos.get(eid, False))
                if open_early_full_count < open_early_min_full_position:
                    continue
                # 指定日需要 14:00 到岗补位（必须是“非白班”的晚班人员）
                cc_only = [eid for eid in cc_set if eid not in bb_set]
                if len(cc_only) < late14_need:
                    continue
                cc_sorted = sorted(cc_only, key=lambda x: rank_key(x, d, "CC"))
                late_14 = set(cc_sorted[:late14_need])

                # 提交该日排班
                for eid in sorted(aa_set):
                    schedule.append(
                        {"employee": eid, "day": d, "shift": "AA", "level": emp_level[eid], "is_senior": emp_level[eid] >= 2}
                    )
                    hours_used[eid] += SHIFT_HOURS["AA"]
                    assigned_shift_count[eid] += 1
                    aa_assigned_count[eid] += 1
                    if d in (6, 7):
                        weekend_assigned[eid] += 1
                for eid in sorted(bb_set):
                    start_h = 10 if eid in open_early else 11
                    schedule.append(
                        {
                            "employee": eid,
                            "day": d,
                            "shift": "BB",
                            "start_hour": start_h,
                            "level": emp_level[eid],
                            "is_senior": emp_level[eid] >= 2,
                        }
                    )
                    hours_used[eid] += SHIFT_HOURS["BB"]
                    assigned_shift_count[eid] += 1
                    if d in (6, 7):
                        weekend_assigned[eid] += 1
                for eid in sorted(cc_set):
                    schedule.append(
                        {
                            "employee": eid,
                            "day": d,
                            "shift": "CC",
                            "start_hour": 14 if eid in late_14 else 17,
                            "level": emp_level[eid],
                            "is_senior": emp_level[eid] >= 2,
                        }
                    )
                    hours_used[eid] += SHIFT_HOURS["CC"]
                    assigned_shift_count[eid] += 1
                    if d in (6, 7):
                        weekend_assigned[eid] += 1
                for eid in (aa_set | bb_set | cc_set):
                    assigned_day_count[eid] += 1
                solved = True
                break
            if solved:
                break

        if not solved:
            raise ValueError(f"第 {d} 天无法满足硬约束，请检查报班或需求设置。")

    return schedule
