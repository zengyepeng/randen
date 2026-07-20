"""燃灯 — Canvas 局部激进重绘器

v6.0 规格书 Module 9.2：替换选中段落，彻底改变句式结构。
激进重写原则：禁用原段落动词/形容词，改变句子长度比例，无缝接入上下文。
"""

from __future__ import annotations

import os
import re
from typing import Any

from .ai_traces_sanitizer import SYNONYM_MAP, sanitize


REDRAWER_SYSTEM_PROMPT = """你是文字缝合怪与二次创作大师。你的任务是替换掉小说中的一段文字，彻底改变原有句式结构。

激进重写原则：
1. 严禁使用原段落中的核心动词和形容词！必须全部替换为同等语义但不相同的词。
2. 改变原段落的句子长度比例——短句变长、长句拆短。
3. 保持原意和剧情推进不变，但表达方式完全重构。
4. 输出段落必须无缝接入前文与后文的语气和节奏。
5. 如果是对话段落，保持说话人身份和核心信息不变，但换一种说法。

输出：仅输出重写后的段落文本，不包含任何解释或标记。"""


def redraw(
    text: str,
    selection: str,
    instruction: str = "",
    llm_client=None,
) -> dict[str, Any]:
    """局部激进重写。

    Args:
        text: 包含选中段落的完整上下文（前文+选中+后文）
        selection: 需要重写的段落
        instruction: 用户指定的重写要求（如 "更紧张一些"、"加一点幽默"）
        llm_client: OpenAI 兼容客户端

    Returns:
        {"redrawn": 重写后的段落, "method": "llm"|"rule", "changes": 修改统计}
    """
    if not selection.strip():
        return {"redrawn": "", "error": "请提供待重写的段落"}

    # 找到选中段落的前后文
    parts = text.split(selection, 1)
    before = parts[0] if len(parts) > 0 else ""
    after = parts[1] if len(parts) > 1 else ""

    # 提取前后文的最后/第一句作为衔接锚点
    before_anchor = _last_sentence(before) if before else ""
    after_anchor = _first_sentence(after) if after else ""

    if llm_client:
        return _llm_redraw(selection, before_anchor, after_anchor, instruction, llm_client)
    else:
        return _rule_redraw(selection, instruction)


def _llm_redraw(
    selection: str,
    before: str,
    after: str,
    instruction: str,
    client,
) -> dict[str, Any]:
    """使用 LLM 进行智能重写。"""
    prompt = REDRAWER_SYSTEM_PROMPT

    if before:
        prompt += f"\n【前文衔接】{before}"
    if after:
        prompt += f"\n【后文衔接】{after}"
    if instruction:
        prompt += f"\n【用户要求】{instruction}"

    prompt += f"\n\n【待重写段落】\n{selection}"

    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=min(len(selection) * 2, 4000),
        )
        result = resp.choices[0].message.content or selection
        return {
            "redrawn": result.strip(),
            "method": "llm",
            "original_len": len(selection),
            "redrawn_len": len(result),
        }
    except Exception:
        return _rule_redraw(selection, instruction)


def _rule_redraw(selection: str, instruction: str = "") -> dict[str, Any]:
    """规则引擎重写——替换核心词汇 + 打乱句式。"""
    result = selection
    changes = 0

    # 1. 同义词替换（激进模式——替换所有匹配的动词/形容词）
    for word, synonyms in SYNONYM_MAP.items():
        if word in result:
            import random
            # 全部替换（不是随机替换）
            while word in result:
                replacement = random.choice(synonyms)
                result = result.replace(word, replacement, 1)
                changes += 1

    # 2. 通过脱敏器做基础变异
    sanitized = sanitize(result, "aggressive")
    result = sanitized["text"]
    changes += sanitized["changes"]

    # 3. 如果指定了 instruction，追加提示
    if instruction:
        result = f"[按「{instruction}」重写]\n{result}"

    return {
        "redrawn": result,
        "method": "rule",
        "changes": changes,
        "original_len": len(selection),
        "redrawn_len": len(result),
        "note": "💡 配置 LLM_API_KEY 获得 AI 智能重写" if not instruction else f"规则重写 + {instruction}",
    }


def _last_sentence(text: str, max_chars: int = 50) -> str:
    """提取最后一句作为衔接锚点。"""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    # 从后往前找最近的句号
    for i in range(len(text) - 1, max(0, len(text) - max_chars * 3), -1):
        if text[i] in "。！？….\n":
            return text[i + 1:].strip()[:max_chars]
    return text[-max_chars:]


def _first_sentence(text: str, max_chars: int = 50) -> str:
    """提取第一句作为衔接锚点。"""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    for i, ch in enumerate(text):
        if ch in "。！？…" and i > 10:
            return text[:i + 1].strip()[:max_chars]
    return text[:max_chars]


# ═══════════════════════════════════════════════════════════
# 批量重写
# ═══════════════════════════════════════════════════════════

def redraw_many(
    text: str,
    selections: list[str],
    instructions: list[str] | None = None,
    llm_client=None,
) -> dict[str, Any]:
    """批量重写多个段落。"""
    results = []
    current_text = text

    for i, sel in enumerate(selections):
        instr = instructions[i] if instructions and i < len(instructions) else ""
        r = redraw(current_text, sel, instr, llm_client)

        if r.get("redrawn") and r["redrawn"] != sel:
            current_text = current_text.replace(sel, r["redrawn"], 1)
            results.append({"index": i, "redrawn": r["redrawn"], "method": r.get("method")})

    return {
        "text": current_text,
        "redraws": results,
        "total_redrawn": len(results),
    }
