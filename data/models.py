"""
数据模型：员工、班次、可用性
"""
from pydantic import BaseModel
from typing import Optional


# 班次类型与时长（小时）
# 开早(10-11)无独立班次，从AA或BB中选3人即可。AA=全天(10-22), BB=白天(11-17), CC=晚班(17-22)
SHIFT_HOURS = {"AA": 12, "BB": 6, "CC": 5}
SHIFT_TIMES = {"AA": (10, 22), "BB": (11, 17), "CC": (17, 22)}


class Employee(BaseModel):
    """员工。is_full_position=True 为全岗，任一小时段至少需1名全岗"""
    id: str
    level: int = 1
    skills: list[str] = []
    max_hours_week: int = 40
    is_full_position: bool = False


class Demand(BaseModel):
    """某天某班次的需求人数"""
    day: int  # 1-7
    shift: str  # AA/BB/CC
    required: int
    min_level: Optional[int] = 1
