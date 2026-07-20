"""燃灯 — 小说转短剧剧本降维打击器

v6.0 规格书 Module 8.2：将小说章节改编为竖屏短剧剧本。
1分钟一集（约1500字），内心描写→动作神态，每集结尾情绪极致卡点。
"""

from __future__ import annotations

import os
from typing import Any


ADAPTOR_PROMPT = """你是千万级爆款短剧的编剧。请将以下小说章节改编为竖屏短剧剧本。

规则：
1. 短剧要求节奏极快，1分钟一集（约1500字剧本）
2. 将小说的内心描写转化为【动作】和【神态】提示
3. 每集结尾必须是情绪极致的卡点（如下跪、扇巴掌、亮出身份、反转）
4. 多用室外场景，少用特效，便于低成本拍摄
5. 对话简洁有力，每句不超过25字
6. 保留原著的核心冲突和爽点

输出格式（标准剧本格式）：
**第 X 集：[集名]**
**场景**：[地点]
**人物**：[出场人物]

[动作描写] 描述...

角色A（情绪/语气）：[台词]
角色B（情绪/语气）：[台词]

..."""


def adapt_chapter_to_drama(
    chapter_text: str,
    chapter_title: str = "",
    episode_count: int = 3,
    llm_client=None,
) -> dict[str, Any]:
    """将小说章节改编为短剧剧本。

    Args:
        chapter_text: 小说章节正文
        chapter_title: 章节标题
        episode_count: 期望的集数
        llm_client: OpenAI 兼容客户端

    Returns:
        {"script": 完整剧本, "episodes": 集数, "used_llm": bool}
    """
    if not chapter_text.strip():
        return {"script": "", "error": "请提供章节正文"}

    if llm_client:
        return _llm_adapt(chapter_text, chapter_title, episode_count, llm_client)
    else:
        return _template_adapt(chapter_text, chapter_title, episode_count)


def _llm_adapt(
    text: str,
    title: str,
    count: int,
    client,
) -> dict[str, Any]:
    """使用 LLM 进行深度改编。"""
    prompt = ADAPTOR_PROMPT + f"""

小说章节{'《' + title + '》' if title else ''}内容：

{text[:8000]}

请将以上内容改编为{count}集短剧剧本。每集独立的场景和冲突，结尾卡在情绪高点。"""

    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=min(count * 1500, 8000),
        )
        result = resp.choices[0].message.content or ""
        return {
            "script": result.strip(),
            "episodes": count,
            "used_llm": True,
            "original_len": len(text),
        }
    except Exception as e:
        return {
            "script": _template_adapt(text, title, count)["script"],
            "episodes": count,
            "used_llm": False,
            "error": str(e)[:100],
        }


def _template_adapt(
    text: str,
    title: str,
    count: int,
) -> dict[str, Any]:
    """本地模板模式——提供结构化改编框架。"""
    lines = text.split("\n")
    # 提取关键场景
    scenes = _extract_key_scenes(lines)

    script_parts = []
    script_parts.append(f"# 短剧剧本：《{title or '未命名'}》改编")
    script_parts.append(f"# 共 {count} 集 | 💡 配置 LLM_API_KEY 获得 AI 深度改编\n")

    for ep in range(1, count + 1):
        scene = scenes[ep - 1] if ep <= len(scenes) else "（待填充）"

        script_parts.append(f"""**第 {ep} 集：{_episode_title(ep, title)}**

**场景**：{_suggest_location(ep)}
**人物**：主角，配角（按需）

[动作描写]
主角{_action_for_episode(ep)}

主角（{_emotion_for_episode(ep)}）：【{scene[:50]}…】

配角（回应）：【台词】

——
[卡点]
{_cliffhanger_for_episode(ep)}

""")

    script_parts.append("\n💡 填入具体台词和对白即可。每集约1500字，控制在1分钟阅读量。")
    return {
        "script": "\n".join(script_parts),
        "episodes": count,
        "used_llm": False,
        "original_len": len(text),
    }


def _extract_key_scenes(lines: list[str]) -> list[str]:
    """从小说文本中提取关键场景。"""
    scenes = []
    current = []

    for line in lines:
        line = line.strip()
        if not line:
            if current and len(current) > 3:
                scenes.append("\n".join(current))
                current = []
            continue

        # 检测场景切换（时间/地点/人物变化）
        if any(w in line for w in ["第二天", "与此同时", "另一边", "转眼", "画面一转",
                                     "客厅", "门口", "街上", "办公室", "房间"]):
            if current:
                scenes.append("\n".join(current))
                current = []
        current.append(line)

    if current:
        scenes.append("\n".join(current))

    return scenes if scenes else ["（未能自动提取场景，请手动标注）"]


def _episode_title(ep: int, title: str) -> str:
    titles = [
        "命运的齿轮", "初次交锋", "身份揭露",
        "绝地反击", "真相大白", "最后一刻",
    ]
    if ep <= len(titles):
        return titles[ep - 1]
    return f"转折 {ep}"


def _suggest_location(ep: int) -> str:
    locations = ["公司办公室", "豪宅客厅", "街头咖啡厅", "废弃工厂", "酒店大堂", "医院走廊"]
    return locations[(ep - 1) % len(locations)]


def _action_for_episode(ep: int) -> str:
    actions = [
        "猛地推开大门，眼神冷峻地扫视在场所有人。",
        "缓步走向对方，每一步都带着压迫感。",
        "当众撕碎手中的文件，碎片如雪花般飘落。",
        "从怀中掏出一枚令牌，在场所有人脸色骤变。",
        "转身准备离开，又突然停住脚步。",
        "单膝跪地，抬起头时眼中已泛起泪光。",
    ]
    return actions[(ep - 1) % len(actions)]


def _emotion_for_episode(ep: int) -> str:
    emotions = ["冷声", "压抑着怒火", "似笑非笑", "语气平静但眼神锋利", "低沉", "颤抖"]
    return emotions[(ep - 1) % len(emotions)]


def _cliffhanger_for_episode(ep: int) -> str:
    cliffhangers = [
        "门被猛然推开，来人竟是——",
        "他手中的照片缓缓翻转，上面的人脸让在场所有人倒吸一口凉气。",
        "手机屏幕亮起，一条消息：「你的真实身份，我已经知道了。」",
        "她缓缓摘下墨镜，露出一张与主角一模一样的面孔。",
        "枪声响起——画面戛然而止。",
        "他笑了：「你以为结束了吗？游戏才刚刚开始。」",
    ]
    return cliffhangers[(ep - 1) % len(cliffhangers)]


# ═══════════════════════════════════════════════════════════
# 批量改编
# ═══════════════════════════════════════════════════════════

def adapt_entire_arc(
    chapters: list[dict[str, str]],
    arc_title: str = "",
    llm_client=None,
) -> dict[str, Any]:
    """将整个篇章的所有章节批量改编为短剧。

    Args:
        chapters: [{"title": "章名", "content": "正文"}, ...]
        arc_title: 篇章名
        llm_client: OpenAI 兼容客户端

    Returns:
        {"scripts": [...], "total_episodes": N}
    """
    results = []
    total_episodes = 0

    for ch in chapters:
        episodes = max(1, len(ch.get("content", "")) // 3000)
        r = adapt_chapter_to_drama(
            ch.get("content", ""),
            ch.get("title", ""),
            episodes,
            llm_client,
        )
        results.append({
            "chapter": ch.get("title", ""),
            "script": r.get("script", ""),
            "episodes": r.get("episodes", 0),
        })
        total_episodes += r.get("episodes", 0)

    return {
        "arc_title": arc_title or "全集",
        "scripts": results,
        "total_chapters": len(chapters),
        "total_episodes": total_episodes,
    }
