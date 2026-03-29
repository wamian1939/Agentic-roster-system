"""
规则建议 Agent：给出可落地的规则修改建议（JSON）
"""
import json
import os
from typing import Dict, List

from openai import OpenAI


def _extract_json(text: str) -> Dict:
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()
    try:
        return json.loads(text)
    except Exception:
        return {"summary": "模型返回非JSON，已保留原文。", "raw_text": text, "suggestions": []}


def run_rule_suggestion_agent(
    rules: List[Dict],
    summary: Dict,
    weight_result: Dict,
    risk_result: Dict,
    model: str = "gpt-4.1-mini",
) -> Dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"summary": "未设置 OPENAI_API_KEY，无法生成规则建议。", "suggestions": []}

    payload = {
        "rules": rules,
        "summary": summary,
        "weight_agent": weight_result,
        "risk_agent": risk_result,
    }
    prompt = (
        "你是规则建议Agent。请基于输入数据输出严格JSON，不要Markdown。"
        "给非技术门店管理者看，表达必须短句、清晰、可执行。"
        "JSON结构为："
        '{"summary":"一句话总建议，不超过35字",'
        '"suggestions":[{"id":"S1","priority":"high|medium|low",'
        '"title":"不超过16字的建议标题",'
        '"plain_advice":"一句话建议，不超过30字",'
        '"why":"一句话原因，不超过26字",'
        '"how_to_apply":"一句话操作，不超过30字",'
        '"target_rule_id":"M_XXX",'
        '"change":{"field":"params.xxx","from":"旧值","to":"新值"}}]}'
        "要求：最多3条建议，优先给 high/medium。"
    )

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", model),
        temperature=0.2,
        messages=[
            {"role": "system", "content": "你是严谨的排班规则优化专家。"},
            {"role": "user", "content": prompt + "\n\n输入:\n" + json.dumps(payload, ensure_ascii=False)},
        ],
    )
    content = resp.choices[0].message.content or ""
    result = _extract_json(content)
    # 兜底：若模型未返回面向非技术用户字段，自动补简化字段
    for s in result.get("suggestions", []):
        if not s.get("title"):
            s["title"] = f"优化 {s.get('target_rule_id', '规则')}"
        if not s.get("plain_advice"):
            ch = s.get("change", {})
            s["plain_advice"] = f"把 {ch.get('field', '参数')} 从 {ch.get('from', '-')} 调到 {ch.get('to', '-')}"
        if not s.get("why"):
            s["why"] = s.get("reason", "让排班更均衡")
        if not s.get("how_to_apply"):
            ch = s.get("change", {})
            s["how_to_apply"] = f"在 {s.get('target_rule_id', '对应规则')} 中修改 {ch.get('field', '参数')}"
    return result
