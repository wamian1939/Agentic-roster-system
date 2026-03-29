"""
排班诊断入口（兼容层）：内部使用多 Agent 协作
"""
from pathlib import Path
from typing import Dict, List, Optional

from core.agents.orchestrator_agent import run_diagnosis_orchestrator


def diagnose_schedule_with_chatgpt(
    schedule: List[Dict],
    employees: list,
    rules_path: Path,
    personal_weights: Optional[Dict[str, float]] = None,
    model: str = "gpt-4.1-mini",
) -> str:
    return run_diagnosis_orchestrator(
        schedule=schedule,
        employees=employees,
        rules_path=rules_path,
        personal_weights=personal_weights or {},
        model=model,
    )
