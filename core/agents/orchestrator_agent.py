"""
协调 Agent：聚合多个子 Agent，再调用 ChatGPT 生成报告
"""
import json
import os
from pathlib import Path
from typing import Dict, List

from openai import OpenAI

from core.agents.common import build_schedule_summary, load_rules
from core.agents.risk_agent import run_risk_agent
from core.agents.weight_agent import run_weight_agent
from core.env_utils import load_project_env


def run_diagnosis_orchestrator(
    schedule: List[Dict],
    employees: list,
    rules_path: Path,
    personal_weights: Dict[str, float],
    model: str = "gpt-4.1-mini",
) -> str:
    load_project_env(Path(__file__).resolve().parent.parent.parent)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("缺少 OPENAI_API_KEY，无法调用 ChatGPT API。")

    summary = build_schedule_summary(schedule, employees)
    rules = load_rules(rules_path)
    weight_result = run_weight_agent(summary, personal_weights, employees)
    risk_result = run_risk_agent(schedule, summary, rules)

    payload = {
        "rules": rules,
        "summary": summary,
        "weight_agent": weight_result,
        "risk_agent": risk_result,
        "employee_count": len(employees),
        "assignment_count": len(schedule),
    }
    prompt = (
        "你是排班系统的协调Agent，需综合多个子Agent结果给出最终诊断。\n"
        "请按以下结构输出：\n"
        "1) 总体评估（3-5句）\n"
        "2) 关键问题（最多6条，按严重度）\n"
        "3) 权重偏差解读（基于weight_agent）\n"
        "4) 规则风险解读（基于risk_agent）\n"
        "5) 可执行优化建议（最多6条，参数级）\n"
        "6) 下周可直接调整的规则片段(JSON)"
    )

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", model),
        temperature=0.2,
        messages=[
            {"role": "system", "content": "你是严谨的排班总控分析师。"},
            {"role": "user", "content": prompt + "\n\n输入数据:\n" + json.dumps(payload, ensure_ascii=False)},
        ],
    )
    return resp.choices[0].message.content or ""
