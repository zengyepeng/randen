"""燃灯 — 章节大纲细化器 + 专精场景路由器 + 情感注入器

v6.0 规格书 Module 6.2 + 7.1 + 7.2
"""

from __future__ import annotations
import os, random, json, re
from typing import Any


# ═══════════════════════════════════════════════════════════
# Module 6.2: 章节大纲细化器
# ═══════════════════════════════════════════════════════════

PACING_TYPES = ["铺垫", "压抑", "爆发", "过渡", "日常"]
NARRATIVE_STRUCTURES = ["线性顺叙", "倒叙揭秘", "双线交叉", "多视角切换", "插叙回忆", "平行蒙太奇"]
CLIFFHANGER_TYPES = ["悬念断章", "危机断章", "反转断章", "情感断章", "揭秘断章"]

CHAPTER_OUTLINER_PROMPT = """你是剧情节奏大师。将卷宗大纲拆解为单章大纲，并设计叙事结构。

卷宗大纲：{volume_outline}
前一章摘要：{previous_summary}
目标字数：{target_words} 字
节奏类型偏好：{pacing_preference}

输出 JSON:
{{
  "chapter_number": {chapter_num},
  "pacing_type": "铺垫/压抑/爆发/过渡/日常",
  "narrative_structure": "线性顺叙/倒叙揭秘/双线交叉/多视角切换",
  "plot_points": ["本章必须发生的剧情节点"],
  "reward_points": ["本章给读者的爽点/情绪高潮"],
  "cliffhanger_type": "悬念断章/危机断章/反转断章",
  "pov_character": "主视角人物",
  "estimated_words": {target_words}
}}"""


def refine_chapter_outline(
    volume_outline: str,
    chapter_num: int,
    previous_summary: str = "",
    target_words: int = 3000,
    pacing_preference: str = "",
    llm_client=None,
) -> dict[str, Any]:
    """细化单章大纲，包含节奏类型和叙事结构。"""
    if llm_client:
        return _llm_outline(volume_outline, chapter_num, previous_summary,
                           target_words, pacing_preference, llm_client)
    return _template_outline(volume_outline, chapter_num, previous_summary, target_words)


def _llm_outline(outline, ch_num, prev, words, pacing, client):
    prompt = CHAPTER_OUTLINER_PROMPT.format(
        volume_outline=outline,
        chapter_num=ch_num,
        previous_summary=prev or "无（第一章）",
        target_words=words,
        pacing_preference=pacing or "自动选择",
    )
    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5, max_tokens=800,
        )
        content = resp.choices[0].message.content or "{}"
        # Try to extract JSON
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            return json.loads(match.group(0))
        return {"chapter_number": ch_num, "raw": content}
    except Exception:
        return _template_outline(outline, ch_num, prev, words)


def _template_outline(outline: str, ch_num: int, prev: str, words: int) -> dict:
    pacing_idx = (ch_num - 1) % len(PACING_TYPES)
    struct_idx = (ch_num - 1) % len(NARRATIVE_STRUCTURES)
    cliff_idx = (ch_num - 1) % len(CLIFFHANGER_TYPES)
    return {
        "chapter_number": ch_num,
        "pacing_type": PACING_TYPES[pacing_idx],
        "narrative_structure": NARRATIVE_STRUCTURES[struct_idx],
        "plot_points": ["自动推进大纲节点", f"基于前期铺垫展开冲突"],
        "reward_points": ["读者期待的爽点兑现"],
        "cliffhanger_type": CLIFFHANGER_TYPES[cliff_idx],
        "pov_character": "主角",
        "estimated_words": words,
        "ai": False,
    }


# ═══════════════════════════════════════════════════════════
# Module 7.1: 专精场景路由器
# ═══════════════════════════════════════════════════════════

SCENE_TYPES = {
    "fight": {
        "name": "战斗场景",
        "prompt_prefix": "你正在写一场战斗。节奏要快，动作要具体（3-5个动作为一组），招式名清晰。避免抽象的力量对轰——每一击都让读者能\"看到\"。",
        "temperature": 0.8,
        "style_rules": ["短句为主", "每段不超过3行", "感官描写：视觉+触觉+听觉"],
    },
    "dialogue": {
        "name": "对话场景",
        "prompt_prefix": "你正在写一段对话。每人说话方式必须独特（通过句式长短、用词习惯区分）。避免所有角色说一样的话。每3句对话插入一个动作/神态。",
        "temperature": 0.7,
        "style_rules": ["短句交锋", "潜台词比明说更重要", "配合微表情"],
    },
    "daily": {
        "name": "日常场景",
        "prompt_prefix": "你正在写日常过渡。不要流水账。从日常中发现不寻常的细节。埋1-2个伏笔线索。保持阅读节奏轻快。",
        "temperature": 0.6,
        "style_rules": ["轻快节奏", "1个不寻常细节", "自然带出1个伏笔线索"],
    },
    "psychology": {
        "name": "心理场景",
        "prompt_prefix": "你正在写角色内心活动。用动作和感官反射内心情绪——不要直接说\"他很难过\"。内心独白不超过2句，其余落地为行为。",
        "temperature": 0.65,
        "style_rules": ["情绪→行为落地", "最多2句内心独白", "穿插环境渲染"],
    },
    "climax": {
        "name": "高潮场景",
        "prompt_prefix": "你正在写本卷/本章的高潮。情绪必须拉到顶点。所有之前的伏笔和铺垫在此刻引爆。结尾必须让读者拍桌。",
        "temperature": 0.85,
        "style_rules": ["情绪极致", "多条伏笔同时爆发", "结尾炸裂"],
    },
    "transition": {
        "name": "过渡场景",
        "prompt_prefix": "你正在写段落过渡。控制在100字以内。快速完成场景切换或时间跳跃。不要在此处展开新细节。",
        "temperature": 0.3,
        "style_rules": ["100字以内", "快速切换", "不展开"],
    },
}


def route_scene(chapter_data: dict[str, Any]) -> dict[str, Any]:
    """根据章节大纲的路由类型，选择对应的场景写作模式。

    Args:
        chapter_data: 包含 pacing_type 的章节大纲数据

    Returns:
        {scene_type, prompt_prefix, temperature, style_rules}
    """
    pacing = chapter_data.get("pacing_type", "过渡")
    mapping = {
        "爆发": "climax",
        "压抑": "psychology",
        "铺垫": "fight",
        "日常": "daily",
        "过渡": "transition",
    }
    scene_key = mapping.get(pacing, "daily")
    scene = SCENE_TYPES[scene_key]
    return {
        "scene_type": scene_key,
        "scene_name": scene["name"],
        "prompt_prefix": scene["prompt_prefix"],
        "temperature": scene["temperature"],
        "style_rules": scene["style_rules"],
    }


def classify_text_scene(text: str) -> dict[str, Any]:
    """分析已有文本，判断属于什么场景类型。"""
    scores = {}
    total_words = len(text.replace(" ", "").replace("\n", ""))

    # 简单规则分类
    if "剑" in text or "拳" in text or "轰" in text or "击" in text:
        scores["fight"] = 1
    if text.count("说") > 3 or text.count("道") > 3:
        scores["dialogue"] = scores.get("dialogue", 0) + 1
    if "想" in text or "觉得" in text or "心里" in text:
        scores["psychology"] = scores.get("psychology", 0) + 1
    if total_words < 200:
        scores["transition"] = scores.get("transition", 0) + 1

    if not scores:
        scores["daily"] = 1

    best = max(scores, key=scores.get)
    return {"scene_type": best, "confidence": scores[best], "all_scores": scores}


# ═══════════════════════════════════════════════════════════
# Module 7.2: 情感注入器
# ═══════════════════════════════════════════════════════════

EMOTION_ANCHORS = {
    "愤怒": {
        "actions": ["指节发白", "牙关紧咬", "呼吸急促", "身体微微发抖", "眼底充血"],
        "expressions": ["脸色铁青", "额头青筋跳动", "嘴角抽搐"],
        "dialogue_hints": ["压低到极致的声音", "一字一顿", "冷笑"],
    },
    "恐惧": {
        "actions": ["手心全是冷汗", "喉咙发干", "腿不听使唤", "后背紧贴墙壁"],
        "expressions": ["瞳孔缩小", "脸色刷白", "嘴唇发抖"],
        "dialogue_hints": ["声音发颤", "语无伦次", "说不完整一句话"],
    },
    "悲伤": {
        "actions": ["肩膀垮下来", "手按住胸口", "慢慢蹲下", "把脸埋进手里"],
        "expressions": ["眼眶发红", "鼻尖泛红", "嘴角向下"],
        "dialogue_hints": ["声音很轻", "断断续续", "说一半就说不下去了"],
    },
    "喜悦": {
        "actions": ["猛地站起来", "来回踱步", "挥舞手臂", "拍桌子"],
        "expressions": ["眼睛亮起来", "嘴角不自觉上扬", "脸上藏不住笑容"],
        "dialogue_hints": ["语速变快", "声音提高", "不自觉地笑出声"],
    },
    "紧张": {
        "actions": ["反复看手表/手机", "指尖轻敲桌面", "不自觉地咬嘴唇", "坐立不安"],
        "expressions": ["眉头紧锁", "眼神飘忽", "面部肌肉紧绷"],
        "dialogue_hints": ["回答简短", "声音紧绷", "顾左右而言他"],
    },
    "震惊": {
        "actions": ["后退一步", "手停在半空", "手里的东西掉落", "猛地转头"],
        "expressions": ["瞳孔放大", "嘴巴微张", "表情僵在脸上"],
        "dialogue_hints": ["说不出一句完整的话", "只蹦出几个词", "声音变了调"],
    },
}

EMOTION_INJECTOR_PROMPT = """你是情感写作专家。将以下情绪转化为具体、可感知的动作、神态和环境渲染。

角色当前情绪：{emotion}
原文片段：{text}

规则：
1. 不要直接说"他很{emotion}"——全部转化为动作和神态
2. 添加至少2个具象感官细节
3. 情绪强度为：{intensity}/10
4. 每个情绪动作必须独特——不要所有角色生气都是"握紧拳头"

输出：仅输出修改后的文本片段。"""


def inject_emotion(
    text: str,
    emotion: str,
    intensity: int = 7,
    llm_client=None,
) -> dict[str, Any]:
    """将抽象情绪转化为具体动作和神态描写。

    Args:
        text: 原文片段
        emotion: 目标情绪 (愤怒/恐惧/悲伤/喜悦/紧张/震惊)
        intensity: 情绪强度 1-10
        llm_client: OpenAI 兼容客户端

    Returns:
        {"text": 情感注入后的文本, "emotion": 情绪, "injections": 注入数量}
    """
    if llm_client:
        return _llm_inject(text, emotion, intensity, llm_client)
    return _rule_inject(text, emotion, intensity)


def _llm_inject(text, emotion, intensity, client):
    prompt = EMOTION_INJECTOR_PROMPT.format(text=text, emotion=emotion, intensity=intensity)
    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        resp = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}],
            temperature=0.7, max_tokens=min(len(text) * 2, 2000),
        )
        return {
            "text": (resp.choices[0].message.content or text).strip(),
            "emotion": emotion,
            "intensity": intensity,
            "used_llm": True,
        }
    except Exception:
        return _rule_inject(text, emotion, intensity)


def _rule_inject(text: str, emotion: str, intensity: int) -> dict[str, Any]:
    """规则引擎情感注入——替换抽象描写为具象动作。"""
    anchor = EMOTION_ANCHORS.get(emotion)
    if not anchor:
        return {"text": text, "emotion": emotion, "injections": 0}

    injections = 0
    result = text

    # 选择注入点（段落中间偏后）
    paragraphs = result.split("\n\n")
    new_paragraphs = []

    for para in paragraphs:
        if not para.strip() or len(para) < 30:
            new_paragraphs.append(para)
            continue

        # 选择随机位置注入动作+神态
        if intensity > 3:
            action = random.choice(anchor["actions"])
            expression = random.choice(anchor["expressions"])

            # 插入位置：段落中间
            mid = len(para) // 2
            dot = para.rfind("。", 0, mid + 20)
            if dot > 0:
                injection = f"他{action}，{expression}。"
                para = para[:dot + 1] + injection + para[dot + 1:]
                injections += 1

        new_paragraphs.append(para)

    return {
        "text": "\n\n".join(new_paragraphs),
        "emotion": emotion,
        "intensity": intensity,
        "injections": injections,
        "used_llm": False,
    }


def inject_emotion_chain(
    text: str,
    emotion_sequence: list[tuple[str, int]],
    llm_client=None,
) -> dict[str, Any]:
    """按情感序列逐段注入（模拟情绪变化曲线）。

    Args:
        text: 原文
        emotion_sequence: [(emotion, intensity), ...]
            如 [("紧张", 3), ("紧张", 6), ("恐惧", 8), ("愤怒", 9)]
        llm_client: 可选 LLM 客户端

    Returns:
        {"text": 注入后文本, "chain": [...每段结果]}
    """
    # 按段落数分配情感
    paragraphs = text.split("\n\n")
    chain_results = []
    result_paras = []

    for i, para in enumerate(paragraphs):
        if not para.strip():
            result_paras.append(para)
            continue

        # 为每个段落分配对应的情感
        idx = min(i * len(emotion_sequence) // max(len(paragraphs), 1),
                   len(emotion_sequence) - 1)
        emotion, intensity = emotion_sequence[idx]
        injected = inject_emotion(para, emotion, intensity, llm_client)
        result_paras.append(injected["text"])
        chain_results.append({
            "paragraph": i,
            "emotion": emotion,
            "intensity": intensity,
            "injections": injected.get("injections", 0),
        })

    return {
        "text": "\n\n".join(result_paras),
        "chain": chain_results,
        "total_injections": sum(c.get("injections", 0) for c in chain_results),
    }
