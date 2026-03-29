"""
应用 AI 规则建议并重新跑 run_demo
stdin: {"overwrite_rules": true}
stdout: {"success": bool, "message": str, ...}
"""
import json
import subprocess
import sys
from pathlib import Path


def main():
    try:
        raw = sys.stdin.read().strip() or "{}"
        payload = json.loads(raw)
        overwrite_rules = bool(payload.get("overwrite_rules", True))

        project_root = Path(__file__).resolve().parent.parent
        rules_path = project_root / "config" / "rules_hard.json"
        sugg_path = project_root / "output" / "rule_suggestions.json"
        if not sugg_path.exists():
            raise ValueError("未找到 output/rule_suggestions.json，请先运行 AI 诊断。")

        from core.agents.rule_apply_agent import apply_and_save_rules

        suggestions = json.loads(sugg_path.read_text(encoding="utf-8")).get("suggestions", [])
        apply_result = apply_and_save_rules(
            rules_path=rules_path,
            suggestions=suggestions,
            overwrite=overwrite_rules,
        )

        run = subprocess.run(
            [sys.executable, str(project_root / "run_demo.py")],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if run.returncode != 0:
            raise RuntimeError(run.stderr.strip() or run.stdout.strip() or "run_demo 执行失败")

        out = {
            "success": True,
            "message": "已应用建议并重新排班。",
            "applied_count": apply_result.get("applied_count", 0),
            "rules_output_path": apply_result.get("output_path"),
            "stdout_tail": (run.stdout or "")[-2000:],
        }
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
    except Exception as e:
        sys.stdout.write(json.dumps({"success": False, "message": str(e)}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
