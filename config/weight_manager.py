"""
权重管理工具：查看、编辑、验证员工权重配置
"""
import json
from pathlib import Path
from typing import Dict, Optional


class WeightManager:
    """员工权重配置管理器"""
    
    def __init__(self, config_path: str = "config/weights_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.weights = self.config.get("weights", {})
    
    def _load_config(self) -> dict:
        """加载配置文件"""
        if not self.config_path.exists():
            print(f"⚠️  配置文件不存在: {self.config_path}")
            return {"weights": {}}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析错误: {e}")
            return {"weights": {}}
    
    def _save_config(self):
        """保存配置文件"""
        self.config["weights"] = self.weights
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        print(f"✓ 配置已保存到 {self.config_path}")
    
    def list_weights(self, sort_by: str = "weight") -> None:
        """
        列出所有员工的权重
        
        Args:
            sort_by: 排序方式 ("weight" 或 "name")
        """
        if not self.weights:
            print("❌ 无权重数据")
            return
        
        items = [(name, weight) for name, weight in self.weights.items()]
        
        if sort_by == "weight":
            items = sorted(items, key=lambda x: x[1], reverse=True)
        else:
            items = sorted(items, key=lambda x: x[0])
        
        print("\n" + "=" * 50)
        print("📊 员工权重配置")
        print("=" * 50)
        print(f"{'员工名称':<20} {'权重':<10} {'优先级':<15}")
        print("-" * 50)
        
        for name, weight in items:
            level = self._weight_to_level(weight)
            print(f"{name:<20} {weight:<10.2f} {level:<15}")
        
        print("=" * 50)
        print("\n权重等级说明：")
        print("  🟥 低  (0.0~0.3): 少排班")
        print("  🟨 普  (0.3~0.5): 中等排班")
        print("  🟩 高  (0.5~0.8): 多排班")
        print("  🟦 顶  (0.8~1.0): 最多排班\n")
    
    def set_weight(self, employee_name: str, weight: float) -> bool:
        """
        设置员工权重
        
        Args:
            employee_name: 员工名称
            weight: 权重值 (0~1)
            
        Returns:
            是否成功
        """
        if not 0 <= weight <= 1:
            print(f"❌ 权重必须在 0~1 之间，您输入: {weight}")
            return False
        
        # 检查员工是否存在
        if employee_name not in self.weights:
            print(f"⚠️  员工 '{employee_name}' 不存在")
            print("   可用的员工列表：")
            for emp in sorted(self.weights.keys()):
                print(f"     - {emp}")
            return False
        
        old_weight = self.weights[employee_name]
        self.weights[employee_name] = weight
        level = self._weight_to_level(weight)
        
        print(f"✓ {employee_name}: {old_weight:.2f} → {weight:.2f} ({level})")
        return True
    
    def add_employee(self, employee_name: str, weight: float = 0.5) -> bool:
        """添加新员工"""
        if employee_name in self.weights:
            print(f"⚠️  员工 '{employee_name}' 已存在，权重: {self.weights[employee_name]}")
            return False
        
        if not 0 <= weight <= 1:
            print(f"❌ 权重必须在 0~1 之间")
            return False
        
        self.weights[employee_name] = weight
        level = self._weight_to_level(weight)
        print(f"✓ 添加员工: {employee_name} (权重: {weight:.2f}, {level})")
        return True
    
    def remove_employee(self, employee_name: str) -> bool:
        """删除员工"""
        if employee_name not in self.weights:
            print(f"❌ 员工 '{employee_name}' 不存在")
            return False
        
        weight = self.weights.pop(employee_name)
        print(f"✓ 已删除员工: {employee_name} (原权重: {weight:.2f})")
        return True
    
    def adjust_batch(self, adjustments: Dict[str, float]) -> None:
        """批量调整权重"""
        success_count = 0
        fail_count = 0
        
        print("\n批量调整权重：")
        for name, weight in adjustments.items():
            if self.set_weight(name, weight):
                success_count += 1
            else:
                fail_count += 1
        
        print(f"\n结果: {success_count} 成功, {fail_count} 失败")
    
    def validate_weights(self) -> bool:
        """验证权重配置的有效性"""
        issues = []
        
        # 检查权重值范围
        for name, weight in self.weights.items():
            if not (0 <= weight <= 1):
                issues.append(f"  ❌ {name}: 权重 {weight} 超出范围 [0, 1]")
        
        # 检查所有权重都相同（可能的问题）
        if self.weights and len(set(self.weights.values())) == 1:
            value = list(self.weights.values())[0]
            if value == 0.5:
                issues.append(f"  ⚠️  所有员工权重都是 {value}（可能是默认值）")
        
        if issues:
            print("\n⚠️  权重配置检查发现问题：")
            for issue in issues:
                print(issue)
            return False
        else:
            print("✓ 权重配置验证通过")
            return True
    
    def get_stats(self) -> dict:
        """获取权重统计信息"""
        if not self.weights:
            return {}
        
        values = list(self.weights.values())
        return {
            "total_employees": len(self.weights),
            "avg_weight": sum(values) / len(values),
            "min_weight": min(values),
            "max_weight": max(values),
            "high_priority_count": sum(1 for w in values if w >= 0.8),
            "low_priority_count": sum(1 for w in values if w < 0.3),
        }
    
    def print_stats(self) -> None:
        """打印权重统计信息"""
        stats = self.get_stats()
        if not stats:
            print("无数据")
            return
        
        print("\n📈 权重统计：")
        print(f"  员工总数: {stats['total_employees']}")
        print(f"  平均权重: {stats['avg_weight']:.2f}")
        print(f"  权重范围: {stats['min_weight']:.2f} ~ {stats['max_weight']:.2f}")
        print(f"  高优先级 (≥0.8): {stats['high_priority_count']}")
        print(f"  低优先级 (<0.3): {stats['low_priority_count']}\n")
    
    @staticmethod
    def _weight_to_level(weight: float) -> str:
        """将权重转换为优先级描述"""
        if weight < 0.3:
            return "🟥 低"
        elif weight < 0.5:
            return "🟨 普通"
        elif weight < 0.8:
            return "🟩 高"
        else:
            return "🟦 顶级"
    
    def export_summary(self, output_path: str = "weights_summary.txt") -> None:
        """导出权重总结"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("员工权重配置总结\n")
            f.write("=" * 50 + "\n\n")
            
            items = sorted(self.weights.items(), key=lambda x: x[1], reverse=True)
            f.write(f"{'员工名称':<20} {'权重':<10} {'优先级':<15}\n")
            f.write("-" * 50 + "\n")
            
            for name, weight in items:
                level = self._weight_to_level(weight)
                f.write(f"{name:<20} {weight:<10.2f} {level:<15}\n")
            
            f.write("\n" + "=" * 50 + "\n")
            stats = self.get_stats()
            f.write(f"平均权重: {stats['avg_weight']:.2f}\n")
            f.write(f"权重范围: {stats['min_weight']:.2f} ~ {stats['max_weight']:.2f}\n")
        
        print(f"✓ 已导出到 {output_path}")


def interactive_edit() -> None:
    """交互式编辑权重"""
    manager = WeightManager()
    
    while True:
        print("\n" + "=" * 50)
        print("📋 权重管理工具")
        print("=" * 50)
        print("1. 查看所有权重")
        print("2. 编辑某个员工的权重")
        print("3. 查看统计信息")
        print("4. 验证配置")
        print("0. 保存并退出")
        print("-" * 50)
        
        choice = input("请选择 (0-4): ").strip()
        
        if choice == "1":
            sort_method = input("按权重(w)还是名字(n)排序? [w]: ").strip().lower()
            sort_by = "name" if sort_method == "n" else "weight"
            manager.list_weights(sort_by)
        
        elif choice == "2":
            name = input("员工名称: ").strip()
            try:
                weight = float(input("新权重 (0~1): ").strip())
                manager.set_weight(name, weight)
            except ValueError:
                print("❌ 无效的权重值")
        
        elif choice == "3":
            manager.print_stats()
        
        elif choice == "4":
            manager.validate_weights()
        
        elif choice == "0":
            manager._save_config()
            print("✓ 已保存，再见！")
            break
        
        else:
            print("❌ 无效的选择")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # 命令行模式
        command = sys.argv[1]
        manager = WeightManager()
        
        if command == "list":
            sort_by = sys.argv[2] if len(sys.argv) > 2 else "weight"
            manager.list_weights(sort_by)
        
        elif command == "set":
            if len(sys.argv) < 4:
                print("用法: python weight_manager.py set <name> <weight>")
            else:
                name = sys.argv[2]
                weight = float(sys.argv[3])
                manager.set_weight(name, weight)
                manager._save_config()
        
        elif command == "stats":
            manager.print_stats()
        
        elif command == "validate":
            manager.validate_weights()
        
        elif command == "export":
            output = sys.argv[2] if len(sys.argv) > 2 else "weights_summary.txt"
            manager.export_summary(output)
        
        else:
            print(f"未知命令: {command}")
            print("可用命令: list, set, stats, validate, export")
    
    else:
        # 交互模式
        interactive_edit()
