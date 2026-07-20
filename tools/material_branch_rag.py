"""燃灯 — 素材智能打标 + 剧情分叉选择器 + RAG检索增强

v6.0 规格书 Module 3.1 + 9.1 + 3.2
"""

from __future__ import annotations
import os, json, re
from pathlib import Path
from typing import Any


# ═══════════════════════════════════════════════════════════
# Module 3.1: 素材结构化与自动打标
# ═══════════════════════════════════════════════════════════

MATERIAL_TAGGER_PROMPT = """你是知识图谱工程师兼网文素材主编。将原始文本转化为结构化写作素材。

原始文本：{raw_text}

输出 JSON:
{{
  "content_essence": "提炼核心内容（100字以内，用于向量化）",
  "source_type": "书籍/新闻/论文/影视/生活观察/游戏/网络讨论",
  "tags": ["#标签1", "#标签2", "#标签3"],
  "applicable_scenarios": ["适用于哪些写作场景"],
  "original_snippet": "保留最具画面感的原文片段（50字以内）"
}}"""

PREDEFINED_TAGS = [
    "#背叛", "#复仇", "#成长", "#逆袭", "#科幻设定", "#硬核物理",
    "#修仙体系", "#都市异能", "#末世生存", "#权谋博弈", "#悬疑揭秘",
    "#人物弧光", "#情感爆发", "#打斗设计", "#日常温馨", "#世界观构建",
    "#反派塑造", "#配角落笔", "#对话技巧", "#节奏控制", "#情绪渲染",
    "#读者爽点", "#勾子设计", "#开篇吸引", "#伏笔回收",
]


def structure_material(
    raw_text: str,
    tags_hint: list[str] | None = None,
    llm_client=None,
) -> dict[str, Any]:
    """将原始文本转化为结构化写作素材（含自动打标）。

    Args:
        raw_text: 原始文本
        tags_hint: 建议标签（可选）
        llm_client: OpenAI 兼容客户端

    Returns:
        结构化素材 dict
    """
    if llm_client:
        return _llm_structure(raw_text, tags_hint, llm_client)
    return _rule_structure(raw_text, tags_hint)


def _llm_structure(text, tags_hint, client):
    prompt = MATERIAL_TAGGER_PROMPT.format(raw_text=text[:2000])
    if tags_hint:
        prompt += f"\n建议标签：{', '.join(tags_hint)}"
    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        resp = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}],
            temperature=0.2, max_tokens=500,
        )
        content = resp.choices[0].message.content or "{}"
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            result = json.loads(match.group(0))
            result["structured_by"] = "llm"
            return result
    except Exception:
        pass
    return _rule_structure(text, tags_hint)


def _rule_structure(text: str, tags_hint: list[str] | None = None) -> dict[str, Any]:
    """规则引擎打标——基于关键词匹配。"""
    # 自动分类
    source_type = "书籍"
    if "新闻" in text or "报道" in text:
        source_type = "新闻"
    elif "论文" in text or "研究" in text:
        source_type = "论文"
    elif "电影" in text or "电视剧" in text:
        source_type = "影视"
    elif "游戏" in text:
        source_type = "游戏"

    # 自动标签匹配
    auto_tags = []
    for tag in PREDEFINED_TAGS:
        keyword = tag.replace("#", "")
        if keyword in text:
            auto_tags.append(tag)
    if tags_hint:
        auto_tags = list(set(auto_tags + tags_hint))
    if not auto_tags:
        auto_tags = ["#世界观构建"]

    # 场景匹配
    scenarios = []
    if "战斗" in text or "打斗" in text or "攻击" in text:
        scenarios.append("适用于写战斗场景")
    if "对话" in text or "交流" in text:
        scenarios.append("适用于对话设计参考")
    if "设定" in text or "规则" in text or "体系" in text:
        scenarios.append("适用于世界观构建")
    if not scenarios:
        scenarios.append("适用于灵感参考")

    # 提取精华片段
    snippet = _extract_vivid_snippet(text)

    return {
        "content_essence": text[:100].replace("\n", " "),
        "source_type": source_type,
        "tags": auto_tags[:5],
        "applicable_scenarios": scenarios,
        "original_snippet": snippet,
        "structured_by": "rule",
    }


def _extract_vivid_snippet(text: str) -> str:
    """提取最具画面感的片段。"""
    sentences = re.split(r"[。！？…\n]", text)
    # 优先找包含感官词汇的句子
    for s in sentences:
        if any(w in s for w in ["看到", "听到", "闻到", "感觉到", "触到", "眼前", "耳边",
                                  "光芒", "黑暗", "声音", "味道", "冰凉", "灼热"]):
            return s.strip()[:50]
    # Fallback
    for s in sentences:
        if len(s) > 10:
            return s.strip()[:50]
    return text[:50]


def batch_structure_materials(
    texts: list[str],
    llm_client=None,
) -> list[dict[str, Any]]:
    """批量结构化多段素材。"""
    return [structure_material(t, llm_client=llm_client) for t in texts]


# ═══════════════════════════════════════════════════════════
# Module 9.1 (extended): 剧情分叉选择器
# ═══════════════════════════════════════════════════════════

BRANCH_PROMPT = """你是剧情设计顾问。根据当前剧情节点，给出3个合理且有创意的剧情发展方向。

当前剧情节点：{current_situation}
角色现状：{character_state}
已埋伏笔：{active_foreshadowing}
作者偏好：{author_preference}

为每个方向提供：
1. 方向描述（30字）
2. 需要的章节数
3. 对读者的情感冲击（1-10）
4. 回收的伏笔数
5. 新增的冲突点

输出 JSON 数组，包含3个选项。"""


def generate_branches(
    current_situation: str,
    character_state: str = "",
    active_foreshadowing: str = "",
    author_preference: str = "",
    llm_client=None,
) -> dict[str, Any]:
    """生成3个剧情分叉方向供作者选择。

    Returns:
        {"branches": [...], "recommendation": 推荐索引}
    """
    if llm_client:
        return _llm_branches(current_situation, character_state,
                            active_foreshadowing, author_preference, llm_client)
    return _template_branches(current_situation, character_state, author_preference)


def _llm_branches(situation, chars, foreshadowing, pref, client):
    prompt = BRANCH_PROMPT.format(
        current_situation=situation,
        character_state=chars or "无特殊状态",
        active_foreshadowing=foreshadowing or "暂无活跃伏笔",
        author_preference=pref or "无特殊偏好",
    )
    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        resp = client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": prompt}],
            temperature=0.8, max_tokens=1200,
        )
        content = resp.choices[0].message.content or "[]"
        match = re.search(r'\[[\s\S]*\]', content)
        if match:
            branches = json.loads(match.group(0))
            return {"branches": branches, "recommendation": 0, "used_llm": True}
    except Exception:
        pass
    return _template_branches(situation, chars, pref)


def _template_branches(situation, chars, pref):
    return {
        "branches": [
            {
                "direction": "高冲突路线——引爆现有矛盾，主动出击",
                "chapters_needed": 3,
                "emotional_impact": 9,
                "foreshadowing_resolved": 2,
                "new_conflicts": 1,
                "description": "主角不再隐忍，直接对抗。节奏加快，爽点密集。适合维持读者热情。"
            },
            {
                "direction": "蓄力路线——埋下更多伏笔，为更大爆发做准备",
                "chapters_needed": 5,
                "emotional_impact": 7,
                "foreshadowing_resolved": 0,
                "new_conflicts": 3,
                "description": "暂缓正面对抗，通过支线丰富世界观和人物关系。适合追求深度。"
            },
            {
                "direction": "反转路线——意想不到的第三方介入，打乱现有格局",
                "chapters_needed": 4,
                "emotional_impact": 8,
                "foreshadowing_resolved": 1,
                "new_conflicts": 2,
                "description": "引入新变数，让读者猜不到下一步。适合需要破局的节点。"
            },
        ],
        "recommendation": 0 if "打斗" in situation or "爆发" in situation else 2,
        "used_llm": False,
        "note": "💡 配置 LLM_API_KEY 获得 AI 深度分叉分析",
    }


# ═══════════════════════════════════════════════════════════
# Module 3.2: RAG 语义检索增强器
# ═══════════════════════════════════════════════════════════

def rag_retrieve(
    query: str,
    materials: list[dict[str, Any]],
    top_k: int = 5,
) -> dict[str, Any]:
    """基于关键词匹配的轻量 RAG 检索（不依赖向量数据库）。

    兜底方案：当嵌入服务不可用时，使用 TF-IDF 风格的关键词匹配。

    Args:
        query: 查询文本
        materials: 素材列表 [{"content_essence": ..., "tags": [...], ...}]
        top_k: 返回 top-K 结果

    Returns:
        {"results": [...], "query": query}
    """
    query_keywords = _extract_keywords(query)

    scored = []
    for i, mat in enumerate(materials):
        score = 0
        text = mat.get("content_essence", "")
        tags = mat.get("tags", [])
        snippet = mat.get("original_snippet", "")
        scenarios = " ".join(mat.get("applicable_scenarios", []))

        combined = f"{text} {' '.join(tags)} {snippet} {scenarios}"

        for kw in query_keywords:
            score += combined.count(kw) * 2
            # Bonus for tag match
            for tag in tags:
                if kw in tag:
                    score += 5

        if score > 0:
            scored.append({"index": i, "score": score, "material": mat})

    scored.sort(key=lambda x: x["score"], reverse=True)

    return {
        "query": query,
        "keywords": query_keywords,
        "results": scored[:top_k],
        "total_matched": len(scored),
    }


def _extract_keywords(text: str, max_kw: int = 10) -> list[str]:
    """中文关键词提取——基于停止词过滤的简单方法。"""
    stop_words = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
                  "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
                  "你", "会", "着", "没有", "看", "好", "自己", "这"}
    # 简单分词：2-4字词组
    keywords = []
    for i in range(len(text)):
        for l in [2, 3, 4]:
            if i + l <= len(text):
                w = text[i:i+l]
                if w not in stop_words and not all(c in "，。！？…、；：""''（）\n " for c in w):
                    keywords.append(w)
    # 按频率排序取 top
    from collections import Counter
    freq = Counter(keywords)
    return [w for w, _ in freq.most_common(max_kw)]


def rag_inject_into_prompt(
    query: str,
    materials: list[dict[str, Any]],
    top_k: int = 3,
) -> str:
    """将 RAG 检索结果注入到写作 Prompt 中。

    Returns:
        可用于注入到 System Prompt 的文本片段
    """
    result = rag_retrieve(query, materials, top_k)

    if not result["results"]:
        return ""

    lines = ["## RAG 参考素材", "以下素材可能在当前章节中有用，请在正文细节中自然体现其设定："]
    for i, r in enumerate(result["results"]):
        m = r["material"]
        lines.append(f"{i+1}. {m.get('content_essence', '')[:80]}")
        snippet = m.get("original_snippet", "")
        if snippet:
            lines.append(f"   📝 {snippet}")
        lines.append(f"   🏷 {', '.join(m.get('tags', [])[:3])}")

    return "\n".join(lines)
