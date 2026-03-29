"""
规则应用 Agent：将规则建议 JSON 应用到规则文件
"""
import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


def _coerce_value(v):
    if isinstance(v, (bool, int, float, list, dict)) or v is None:
        return v
    s = str(v).strip()
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    try:
        if "." in s:
            return float(s)
        return int(s)
    except Exception:
        pass
    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
        try:
            return json.loads(s)
        except Exception:
            return s
    return s


def _set_path(obj: Dict, path: List[str], value) -> Tuple[bool, object]:
    cur = obj
    for k in path[:-1]:
        if not isinstance(cur, dict) or k not in cur:
            return False, None
        cur = cur[k]
    if not isinstance(cur, dict):
        return False, None
    old = cur.get(path[-1])
    cur[path[-1]] = value
    return True, old


def _resolve_rule_path(field: str) -> List[str]:
    field = (field or "").strip()
    if field.startswith("params."):
        return ["constraint", "params"] + field[len("params."):].split(".")
    if field.startswith("constraint."):
        return field.split(".")
    return field.split(".")


def apply_rule_suggestions(rules: List[Dict], suggestions: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    new_rules = copy.deepcopy(rules)
    by_id = {r.get("id"): r for r in new_rules}
    applied = []
    for s in suggestions or []:
        rid = s.get("target_rule_id")
        ch = s.get("change", {})
        field = ch.get("field")
        if not rid or not field or rid not in by_id:
            continue
        path = _resolve_rule_path(field)
        ok, old = _set_path(by_id[rid], path, _coerce_value(ch.get("to")))
        if ok:
            applied.append({
                "suggestion_id": s.get("id"),
                "target_rule_id": rid,
                "field": field,
                "from": old,
                "to": ch.get("to"),
            })
    return new_rules, applied


def apply_and_save_rules(rules_path: Path, suggestions: List[Dict], overwrite: bool = False) -> Dict:
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    new_rules, applied = apply_rule_suggestions(rules, suggestions)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = rules_path if overwrite else rules_path.with_name(f"{rules_path.stem}.ai.{ts}{rules_path.suffix}")
    if overwrite:
        backup = rules_path.with_name(f"{rules_path.stem}.bak.{ts}{rules_path.suffix}")
        backup.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
    target.write_text(json.dumps(new_rules, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"applied_count": len(applied), "applied": applied, "output_path": str(target)}
