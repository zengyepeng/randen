"""燃灯 — 多 Agent 谈判模拟器

v6.0 规格书 Module 7.1：专治权谋戏、多方对话场景。
模拟多角色基于立场和情报差进行心理博弈与对话交锋。
"""

from __future__ import annotations

import json
import os
from typing import Any


NEGOTIATOR_SYSTEM_PROMPT = """你是剧本杀导演兼对白设计大师。你的任务是模拟{char_count}个角色在特定局势下的对话交锋。

核心原则：
1. 每个角色必须严格基于自己的立场、目标和情报差发言
2. 对话必须有来有回：试探 → 反讽 → 抛出筹码 → 隐晦威胁 → 摊牌
3. 严禁上帝视角让步——角色不能说他们"不应该知道"的信息
4. 对话节奏：快速交锋，短句为主，潜台词比明说更重要
5. 融入非语言细节：微表情、小动作、语气变化

输出格式：
[角色名]：[台词] （可选：动作/神态描写）
[角色名]：[台词]

仅输出对话记录，不要包含场景描述或解释。"""


def simulate_negotiation(
    situation: str,
    characters: list[dict[str, Any]],
    llm_client=None,
    rounds: int = 6,
) -> dict[str, Any]:
    """模拟多角色谈判对话。

    Args:
        situation: 当前局势描述
        characters: 参与角色列表，每个角色包含:
            - name: 角色名
            - stance: 立场和态度 (如 "蛰伏复仇,表面恭敬实则试探")
            - goal: 本轮对话目标
            - secret: 角色知道但其他人不知道的情报
            - style: 说话风格 (如 "阴阳怪气", "直来直去", "话里有话")
        llm_client: OpenAI 兼容客户端
        rounds: 期望的交锋轮数

    Returns:
        {"dialogue": 对话文本, "turns": 轮数, "used_llm": bool}
    """
    if not characters or len(characters) < 2:
        return {"dialogue": "", "error": "至少需要2个角色", "used_llm": False}

    if llm_client:
        return _llm_negotiation(situation, characters, llm_client, rounds)
    else:
        return _template_negotiation(situation, characters)


def _llm_negotiation(
    situation: str,
    characters: list[dict[str, Any]],
    client,
    rounds: int,
) -> dict[str, Any]:
    """使用 LLM 进行高质量谈判模拟。"""
    char_profiles = []
    for i, c in enumerate(characters):
        profile = f"""
角色{i+1}: {c['name']}
- 立场: {c.get('stance', '中立')}
- 目标: {c.get('goal', '达成自己的目的')}
- 独家情报: {c.get('secret', '无')}
- 说话风格: {c.get('style', '正常')}"""
        char_profiles.append(profile)

    prompt = NEGOTIATOR_SYSTEM_PROMPT.format(char_count=len(characters)) + f"""

当前局势：{situation}

参与角色及立场：
{''.join(char_profiles)}

请模拟{rounds}轮以内的对话交锋，让每个角色至少发言2次。"""

    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=2000,
        )
        dialogue = resp.choices[0].message.content or ""
        return {
            "dialogue": dialogue.strip(),
            "used_llm": True,
            "character_count": len(characters),
        }
    except Exception as e:
        return {"dialogue": _template_negotiation(situation, characters)["dialogue"],
                "used_llm": False, "error": str(e)[:100]}


def _template_negotiation(
    situation: str,
    characters: list[dict[str, Any]],
) -> dict[str, Any]:
    """本地模板模式——提供结构化的对话框架。"""
    parts = [f"【局势】{situation}\n"]
    parts.append(f"【参与角色】{', '.join(c['name'] for c in characters)}\n")

    for c in characters:
        parts.append(f"""
{c['name']}:
- 立场: {c.get('stance', '未知')}
- 目标: {c.get('goal', '未知')}
- 独家情报: {c.get('secret', '无')}
- 风格: {c.get('style', '正常')}""")

    # 自动生成对话框架
    parts.append("\n---\n【对话框架】（💡 配置 LLM_API_KEY 获得 AI 实时博弈模拟）\n")

    # 第一轮：试探
    parts.append(f"[{characters[0]['name']}]：（率先开口，试探对方意图）")
    parts.append(f"[{characters[1]['name']}]：（回应，同时抛出反试探）")

    # 中间轮：筹码交换
    for i, c in enumerate(characters[2:], 2):
        parts.append(f"[{c['name']}]：（根据自己的立场{_short_stance(c)}，介入对话）")

    # 最终轮：摊牌或僵持
    parts.append(f"[{characters[0]['name']}]：（亮出底牌/给出最后通牒）")
    parts.append(f"\n💡 填入具体台词即可。每个角色的话要符合其立场和情报差。")

    return {
        "dialogue": "\n".join(parts),
        "used_llm": False,
        "character_count": len(characters),
    }


def _short_stance(c: dict) -> str:
    stances = {
        "蛰伏复仇": "隐忍观察",
        "狂妄试探": "步步紧逼",
        "墙头草": "见风使舵",
        "暗中观察": "不动声色",
        "表面恭敬实则试探": "话里有话",
        "敌对": "针锋相对",
        "友好": "释放善意",
        "中立": "谨慎观望",
    }
    return stances.get(c.get("stance", ""), c.get("stance", ""))


# ═══════════════════════════════════════════════════════════
# 谈判强度分析
# ═══════════════════════════════════════════════════════════

def analyze_negotiation(dialogue: str) -> dict[str, Any]:
    """分析一段谈判对话的质量。"""
    characters = set()
    turns = 0
    threats = 0
    deals = 0

    for line in dialogue.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Count turns (lines that start with [Character])
        if line.startswith("[") and "]" in line[:40]:
            char_name = line[1:line.index("]")]
            characters.add(char_name)
            turns += 1

        # Count negotiation tactics
        if any(w in line for w in ["威胁", "警告", "别怪", "后果自负", "试试看", "代价"]):
            threats += 1
        if any(w in line for w in ["合作", "交易", "条件", "利益", "共赢", "好处"]):
            deals += 1

    score = min(100, turns * 8 + len(characters) * 10 + (threats + deals) * 5)

    return {
        "turns": turns,
        "characters_involved": len(characters),
        "threats_detected": threats,
        "deals_proposed": deals,
        "complexity_score": score,
        "verdict": "高张力对话" if score >= 60 else "中等复杂度" if score >= 30 else "对话偏简单",
    }
