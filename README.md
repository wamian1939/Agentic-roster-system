# AI 排班 Demo（精简版）

只保留你的 **排班算法 + Agent + Demo 前端（schedule.html）**。

## 1) 安装

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 2) AI 配置（可选）

在 `.env` 中配置：

```bash
OPENAI_API_KEY=你的key
OPENAI_MODEL=gpt-4.1-mini
ENABLE_AI_DIAGNOSIS=1
```

## 3) 生成排班

```bash
python run_demo.py
```

输出：
- `output/schedule.html`（demo 前端）
- `output/diagnosis.md`（AI复核）
- `output/rule_suggestions.json`（规则建议）

## 4) 一键 Apply 建议并自动重排

先启动本地 apply 服务：

```bash
python integration/demo_apply_server.py
```

然后打开 `output/schedule.html`，点击 **Apply建议并重排**。

## 班次编码

- `AA` 全天（10:00-22:00）
- `BB` 白天（11:00-17:00）
- `CC` 晚班（17:00-22:00）
- 数字 `1-7` 代表周一到周日

## 项目结构

```text
Molly/
├── config/
├── core/
├── data/
├── integration/
├── output/
└── run_demo.py
```
