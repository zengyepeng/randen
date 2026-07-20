"""燃灯 AI 设定助手 — 故事/人物/世界观 三合一体

为 Studio 侧栏「设定」分区（故事/人物/世界）提供 AI 辅助能力。
每个助手独立运作，可单独调用或串联使用。
"""

from __future__ import annotations

import json
import os
import re
from typing import Any


# ═══════════════════════════════════════════════════════════
# 1. 故事助手 (Story Assistant)
# ═══════════════════════════════════════════════════════════

def story_assist(action: str, content: str = "", extra: dict | None = None,
                 llm_client=None) -> dict[str, Any]:
    """故事 AI 助手

    actions:
        - "background": 基于一句话展开故事背景
        - "outline": 基于背景展开篇章大纲
        - "expand_theme": 展开核心主题
        - "author_intent": 生成作者意图声明
        - "current_focus": 生成近期创作罗盘
    """
    if not llm_client:
        return _local_story_fallback(action, content, extra)

    prompts = {
        "background": f"""你是一位资深小说编辑。请将以下一句话灵感，展开成约200字的故事背景设定。

要求：说清楚这个世界的基本规则、核心冲突、以及主角所处的位置。

灵感：{content}

直接输出背景设定，不需要任何前缀说明。""",

        "outline": f"""你是一位大纲专家。基于以下故事背景，生成一份3篇章的小说大纲。

每篇包含：篇名、核心目标、预估章数、关键事件。

背景：{content}

直接输出大纲，格式：
## 第一篇：xxx (约30章)
目标：xxx
关键事件：xxx
## 第二篇：xxx (约50章)
...
## 第三篇：xxx (约40章)
...""",

        "author_intent": f"""你是作品定位顾问。基于以下故事背景，生成一份「作者创作意图」声明。

背景：{content}

格式：
- 我想写给谁看：
- 我想让他们感受到什么：
- 这个故事和其他同类型作品的区别在于：
- 我的核心承诺给读者的是：""",

        "current_focus": f"""你是创作规划师。基于故事背景，为接下来1-2周的写作设定一个清晰的「创作罗盘」。

背景：{content}

输出格式：
- 当前阶段目标：
- 必须保留的元素：
- 必须避免的陷阱：
- 本周写作计划：""",
    }

    prompt = prompts.get(action, f"请分析以下内容并给出建议：\n{content}")

    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        response = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000,
        )
        result = response.choices[0].message.content or ""
        return {"ok": True, "action": action, "result": result.strip(), "ai": True}
    except Exception as e:
        return {"error": f"AI 调用失败: {str(e)[:100]}"}


def _local_story_fallback(action: str, content: str, extra: dict | None = None) -> dict:
    """故事助手本地降级"""
    if action == "background":
        return {"ok": True, "action": action, "result": f"【故事背景草稿】\n\n基于灵感：「{content[:50]}...」\n\n💡 本地模式提示：请配置 LLM_API_KEY 以获得 AI 深度生成。\n\n建议方向：\n1. 明确核心冲突——主角想要什么，什么在阻止他？\n2. 设定世界的基本规则——这个世界和现实有什么不同？\n3. 确立基调——热血？悬疑？温暖？苍凉？", "ai": False}
    if action == "outline":
        return {"ok": True, "action": action, "result": "【大纲草稿】\n\n💡 本地模式 — 请配置 LLM 获得完整大纲生成。\n\n建议结构：\n## 第一篇：入局 (30章) — 主角获得能力/地位改变，建立初期的冲突和关系\n## 第二篇：发展 (50章) — 冲突升级，主角成长，世界观展开\n## 第三篇：高潮与收尾 (40章) — 伏笔回收，终极挑战，角色弧光完成", "ai": False}
    return {"ok": True, "action": action, "result": f"💡 本地模式 — 请配置 LLM_API_KEY 获得 AI 深度生成。", "ai": False}


# ═══════════════════════════════════════════════════════════
# 2. 人物助手 (Character Assistant)
# ═══════════════════════════════════════════════════════════

def character_assist(action: str, content: str = "", extra: dict | None = None,
                     llm_client=None) -> dict[str, Any]:
    """人物 AI 助手

    actions:
        - "create": 基于一句话创建角色档案
        - "relationship": 分析/生成角色关系
        - "dialogue_sample": 生成角色对话样本
        - "arc": 生成角色成长弧
    """
    if not llm_client:
        return _local_char_fallback(action, content, extra)

    prompts = {
        "create": f"""你是角色设计师。请基于以下描述，创建一份完整的角色档案，用 YAML 格式输出。

描述：{content}

输出格式 (YAML):
name: 角色名
identity: 身份
age: 年龄段
personality: 性格描述 (50字)
goal: 核心目标
flaw: 性格缺陷
secret: 隐藏的秘密
catchphrase: 口头禅/标志性动作
appearance: 外貌特征
background_summary: 背景简介 (100字)""",

        "dialogue_sample": f"""你是对白设计师。请为以下角色写3段不同场景的对话样本，体现其性格和说话方式。

角色信息：{content}

输出3段对话：
场景1（日常）：
场景2（冲突）：
场景3（独白）：""",

        "arc": f"""你是角色成长规划师。请为以下角色设计一条从开篇到结局的成长弧线。

角色：{content}

格式：
- 开篇状态：
- 触发事件（是什么改变了他/她）：
- 成长阶段1（前30%）：
- 成长阶段2（30-70%）：
- 至暗时刻（70-90%）：
- 结局状态（如何不同了）：
- 成长主题（一句话总结）：""",
    }

    prompt = prompts.get(action, f"请分析以下角色并给出建议：\n{content}")

    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        response = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=800,
        )
        result = response.choices[0].message.content or ""
        return {"ok": True, "action": action, "result": result.strip(), "ai": True}
    except Exception as e:
        return {"error": f"AI 调用失败: {str(e)[:100]}"}


def _local_char_fallback(action: str, content: str, extra: dict | None = None) -> dict:
    if action == "create":
        return {"ok": True, "action": action, "result": f"【角色档案模板】\n\n基于描述：「{content[:50]}...」\n\n💡 本地模式 — 请配置 LLM 获得完整角色生成。\n\nname: （填写）\nidentity: （身份）\npersonality: （性格）\ngoal: （目标）\nflaw: （缺陷）\nsecret: （秘密）\ncatchphrase: （口头禅）", "ai": False}
    return {"ok": True, "action": action, "result": f"💡 本地模式 — 请配置 LLM_API_KEY", "ai": False}


# ═══════════════════════════════════════════════════════════
# 3. 世界观助手 (World Assistant)
# ═══════════════════════════════════════════════════════════

def world_assist(action: str, content: str = "", extra: dict | None = None,
                 llm_client=None) -> dict[str, Any]:
    """世界观 AI 助手

    actions:
        - "rules": 生成世界规则体系
        - "timeline": 生成历史时间线
        - "geography": 生成地理/区域设定
        - "terminology": 生成术语表
        - "entity": 生成世界观实体
    """
    if not llm_client:
        return _local_world_fallback(action, content, extra)

    prompts = {
        "rules": f"""你是世界观设计师。请基于以下故事背景，设计一套世界规则体系。

背景：{content}

输出格式 (YAML):
magic_system: (魔法/力量体系描述 — 50字)
magic_rules: (核心规则 — 3条)
social_structure: (社会结构)
technology_level: (科技水平)
forbidden_zones: (禁忌/禁区 — 2个)
unique_law: (一条独特的法则)""",

        "timeline": f"""你是世界观历史学家。请基于以下世界设定，生成一条从远古到故事起点的大事件时间线。

世界设定：{content}

输出格式（按时间顺序，5-8个关键节点）：
- 远古纪元：xxx
- 中古时代：xxx
- 近代转折：xxx
- 故事起点前N年：xxx
- 故事起点：xxx""",

        "terminology": f"""你是术语专家。请为以下世界生成一份10个核心术语的术语表。

世界设定：{content}

输出格式：
- 术语1：定义 (20字)
- 术语2：定义 (20字)
...""",

        "entity": f"""你是世界观构建者。请基于以下设定，创建3个重要的世界观实体（如组织、地点、种族、传说物品等）。

背景：{content}

输出3个实体，每个包含：名称、类型、一句话描述、故事相关性说明。""",
    }

    prompt = prompts.get(action, f"请分析以下世界设定并给出建议：\n{content}")

    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        response = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1000,
        )
        result = response.choices[0].message.content or ""
        return {"ok": True, "action": action, "result": result.strip(), "ai": True}
    except Exception as e:
        return {"error": f"AI 调用失败: {str(e)[:100]}"}


def _local_world_fallback(action: str, content: str, extra: dict | None = None) -> dict:
    return {"ok": True, "action": action, "result": f"💡 本地模式 — 请配置 LLM_API_KEY 获得 AI 深度生成。", "ai": False}
