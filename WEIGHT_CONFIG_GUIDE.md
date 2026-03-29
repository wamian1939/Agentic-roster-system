# 🎯 权重配置管理指南

## 📁 新增文件

- `config/weights_config.json` - 权重配置文件（中央配置）
- `config/weight_manager.py` - 权重管理工具
- 修改 `run_demo.py` - 现在从配置文件读取权重

---

## 🚀 快速开始

### 方式1：查看当前权重

```bash
python config/weight_manager.py list
```

输出：
```
==================================================
📊 员工权重配置
==================================================
员工名称             权重       优先级
--------------------------------------------------
Winnie Wang          0.96       🟦 顶
Maomao Wu            0.90       🟦 顶
Jack Li              0.90       🟦 顶
Tina Gu              0.80       🟦 顶
...
Judy Zhu             0.10       🟥 低
```

### 方式2：调整单个员工权重

```bash
# 将 Judy Zhu 的权重从 0.1 改为 0.5
python config/weight_manager.py set "Judy Zhu" 0.5
```

### 方式3：交互式编辑（推荐）

```bash
python config/weight_manager.py
```

会进入菜单界面：
```
==================================================
📋 权重管理工具
==================================================
1. 查看所有权重
2. 编辑某个员工的权重
3. 查看统计信息
4. 验证配置
0. 保存并退出
```

### 方式4：查看统计信息

```bash
python config/weight_manager.py stats
```

输出：
```
📈 权重统计：
  员工总数: 18
  平均权重: 0.59
  权重范围: 0.10 ~ 0.96
  高优先级 (≥0.8): 5
  低优先级 (<0.3): 1
```

---

## 📊 权重配置文件结构

`config/weights_config.json`：

```json
{
  "description": "员工权重配置（0~1，越高越优先排班）",
  "last_updated": "2026-03-29",
  "weights": {
    "Winnie Wang": 0.96,
    "Maomao Wu": 0.9,
    "Judy Zhu": 0.1,
    ...
  },
  "notes": "权重说明...\n..."
}
```

**修改权重的三种方式：**

#### 方式1️⃣：编辑 JSON 文件（推荐）

直接打开 `config/weights_config.json`，修改权重值：

```json
"Judy Zhu": 0.1,  →  "Judy Zhu": 0.5,
```

保存后，下次運行 `run_demo.py` 自動讀取新权重。

#### 方式2️⃣：命令行工具

```bash
python config/weight_manager.py set "Judy Zhu" 0.5
```

#### 方式3️⃣：交互式菜单

```bash
python config/weight_manager.py
# 选择 "2. 编辑某个员工的权重"
```

---

## ⚖️ 权重含义

| 权重范围 | 优先级 | 说明 | 预期排班次数 |
|---------|--------|------|----------|
| 0.0~0.3 | 🟥 低 | 很少排班 | 1~3 班/周 |
| 0.3~0.5 | 🟨 普通 | 中等排班 | 3~5 班/周 |
| 0.5~0.8 | 🟩 高 | 经常排班 | 5~7 班/周 |
| 0.8~1.0 | 🟦 顶级 | 最多排班 | 7+ 班/周 |

**示例：**
- `0.1` - Judy Zhu: 想少上班 → 可能只排 1~2 班
- `0.5` - Junbin Wu: 平均分配 → 排 3~4 班
- `0.96` - Winnie Wang: 全岗 + 高优先级 → 排最多班

---

## 🔧 常见操作

### 查看哪些员工下周会多上班

```bash
python config/weight_manager.py stats
```

查看"高优先级"数量和"平均权重"。

### 批量降低某些人的权重

编辑 `weights_config.json`，然后：

```bash
python config/weight_manager.py validate
```

验证修改是否有效。

### 导出权重总结

```bash
python config/weight_manager.py export weights_summary.txt
```

生成可读文本文件，方便分享给团队。

---

## 🎯 权重调整工作流

```
1️⃣  查看当前权重配置
   python config/weight_manager.py list
   
2️⃣  根据需要调整权重
   - 直接编辑 weights_config.json，或
   - 使用 python config/weight_manager.py set "Name" 0.5
   
3️⃣  验证配置
   python config/weight_manager.py validate
   
4️⃣  运行排班
   python run_demo.py
   
5️⃣  查看排班结果
   打开 output/schedule.html
   
6️⃣  如果不满意，回到步骤 2️⃣
```

---

## 📝 权重调整建议

### 场景1：某员工请假，要减少排班

```bash
# 交互方式
python config/weight_manager.py
# 选择 2，输入员工名和新权重（如 0.2）

# 或直接
python config/weight_manager.py set "员工名" 0.2
```

### 场景2：新员工加入，权重不确定

```bash
# 设为平均值 0.5
python config/weight_manager.py set "新员工名" 0.5
```

### 场景3：全岗员工想少排班

```bash
# 他们自带全岗加分 0.5，所以基础权重应该低一些
# 比如改为 0.3
python config/weight_manager.py set "全岗员工名" 0.3
```

### 场景4：查看权重调整的影响

修改权重后直接运行：
```bash
python run_demo.py
```

查看 `output/schedule.html`，看不同权重的员工排班情况是否符合预期。

---

## ✅ 权重配置最佳实践

✓ **DO:**
- 定期检查权重配置是否合理
- 根据员工请假/加班情况动态调整
- 保存权重历史（用 Git）
- 验证权重后再运行排班

✗ **DON'T:**
- 所有权重设为一样值（0.5） - 失去区分作用
- 权重落在 0 或 1 - 应用 0.1~0.9 范围
- 忘记保存配置文件
- 不验证直接运行

---

## 🐛 常见问题

**Q: 修改权重后排班没变化？**  
A: 确保保存了 `config/weights_config.json`，然后重新运行 `run_demo.py`。

**Q: 权重设为 0 会怎样？**  
A: 该员工基本不会被排班（除非必要排班不满足）。使用 0.1 来表示"很少"。

**Q: 权重设为 1 会怎样？**  
A: 该员工会被优先排班。但如果他报班数量少，实际排班可能还是不多。

**Q: 全岗员工权重应该怎么设？**  
A: 全岗员工自动加 0.5，所以如果想让他们中等排班，设 0.3~0.4；想多排班，设 0.5~0.6。

**Q: 如何确保权重配置正确？**  
A: 
```bash
python config/weight_manager.py validate
```

---

## 🚀 下一步

✅ 权重配置已移到文件  
✅ 可以通过工具快速调整  
✅ 修改后 `run_demo.py` 自动读取

下一步可以：
1. 尝试调整权重，看排班结果的变化
2. 使用权重工具导出总结分享给团队
3. 考虑定时任务自动运行排班
