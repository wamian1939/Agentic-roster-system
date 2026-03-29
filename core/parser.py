"""
报班解析器：将 1234AA67BB 解析为可用性矩阵 A[employee, day, shift]
"""
import re
from typing import Dict, Set, Tuple
# SHIFT_HOURS 在 models 中定义，解析器不直接依赖


def _normalize_availability(raw: str) -> str:
    """
    归一化报班字符串：
    - 转大写（兼容 aa/bb/cc）
    - 去除空格、逗号、中文逗号、分号、斜杠、竖线等常见分隔符
    """
    if not raw:
        return ""
    s = raw.upper()
    # 仅清理常见“视觉分隔符”，不移除数字和字母
    return re.sub(r"[\s,，;；/|]+", "", s)


def parse_availability(raw: str) -> Dict[Tuple[int, str], bool]:
    """
    解析报班字符串，返回 {(day, shift): True} 的可用集合。
    例: "1234AA67BB" → {(1,AA),(2,AA),(3,AA),(4,AA),(6,BB),(7,BB)}
    """
    result: Dict[Tuple[int, str], bool] = {}
    normalized = _normalize_availability(raw)

    # 按 "数字段+班次" 拆分，如 1234AA, 67BB
    pattern = re.compile(r"(\d+)(AA|BB|CC)")
    for match in pattern.finditer(normalized):
        days_str, shift = match.group(1), match.group(2)
        for d in days_str:
            day = int(d)
            if 1 <= day <= 7:
                result[(day, shift)] = True
    return result


def build_availability_matrix(
    employees: list, availability_raw: Dict[str, str]
) -> Dict[Tuple[str, int, str], int]:
    """
    构建 A[e,d,s] ∈ {0,1}，表示员工 e 在 day d 的 shift s 是否可用。
    返回格式: {(e_id, day, shift): 1 或 0}
    """
    A = {}
    for emp in employees:
        raw = availability_raw.get(emp.id, "")
        avail = parse_availability(raw)
        for day in range(1, 8):
            for shift in ["AA", "BB", "CC"]:
                key = (emp.id, day, shift)
                A[key] = 1 if (day, shift) in avail else 0
    return A


# 简单测试
if __name__ == "__main__":
    r = parse_availability("14AA67BB")
    print("14AA67BB →", sorted(r.keys()))
