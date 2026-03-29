"""
规则执行引擎：将 JSON 规则通过 registry 映射到可执行约束
"""
import json
from pathlib import Path
from typing import Any, Callable, Dict, List

REGISTRY: Dict[str, Callable] = {}


def register(name: str):
    def decorator(fn: Callable):
        REGISTRY[name] = fn
        return fn
    return decorator


def load_rules(rules_path: Path) -> List[Dict]:
    """加载 JSON 规则文件"""
    with open(rules_path, encoding="utf-8") as f:
        return json.load(f)


def get_builder(rule: Dict) -> Callable:
    """根据规则获取对应的约束构建函数"""
    name = rule["constraint"]["name"]
    if name not in REGISTRY:
        raise ValueError(f"未知约束类型: {name}，请确保已注册")
    return REGISTRY[name]


def build_constraints_from_rules(
    rules: List[Dict], model, x_vars, context: Dict
) -> None:
    """
    遍历规则，通过 registry 调用对应函数，将约束加入 model。
    context 包含: A(可用矩阵), R(需求), employees, shift_hours 等
    """
    for rule in rules:
        if rule.get("type") != "hard":
            continue
        fn = get_builder(rule)
        params = rule.get("constraint", {}).get("params", {})
        fn(model, x_vars, context, params)
