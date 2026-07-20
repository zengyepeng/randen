"""燃灯 — 写作铁律编译器

v6.0 规格书 Module 4：将 craft/ 中的规则编译为全局 System Prompt，
在每次写章前注入到 LLM 上下文中。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# 内联铁律（如果 craft/ 文件不可用时的后备）
INLINE_IRON_RULES = """# 网文写作铁律与原创性红线

## 1. 表达降维
- 展示而非告知。不要说"他很愤怒"，要写"他指尖掐入掌心，血丝渗出"
- 禁用总结性结尾。不让 AI 写"这一天对他来说意义非凡"
- 感官锚定：每个场景至少触发三种感官描写
- 用具体动作代替抽象心理——"他紧张"→"他的手心全是汗"

## 2. 原创性负面清单
严禁使用以下高中频 AI 废词：
- "倒吸一口凉气" → 用具体身体反应替代
- "虎躯一震" → 用真实动作替代
- "不由得"、"不禁" → 直接删除或改写
- "微微一笑"、"嘴角微扬" → 每角色有独特的笑法
- "眼中闪过一丝" → 直接写眼神变化
- "心中暗想" → 融入动作或直接写想法
- "缓缓"→ 少用悬浮副词
- "然而" → 换口语转折
- "综上所述"、"由此可见"、"值得注意的是"
拒绝套路桥段：
- 反派只会冷哼
- 路人只会惊叹
- 打脸只有震惊
结构变异：
- 打破线性平铺，偶尔倒叙/插叙
- 句式长短参差，不要全是工整对称句

## 3. 毒点红线（绝对禁止）
- 主角圣母心软放过敌人
- 主动送女/绿帽情节
- 主角无逻辑降智
- 大段说教文青病
- 关键战斗回合含糊带过

## 4. 实体锁定
- 书中专有名词、人物名、功法名必须 100% 匹配字典
- 严禁生造新名词——每个新名词必须先在 src/ 中注册
- 未注册的配角/物品一律用代称（"一个青年"、"一把剑"）"""


def compile_iron_rules(project_root: Path | None = None, include_craft: bool = True) -> str:
    """编译铁律为 System Prompt。

    优先从 craft/ 目录加载，fallback 到内联规则。
    """
    rules = []

    if include_craft and project_root:
        craft_dir = project_root / "craft"
        if craft_dir.is_dir():
            for f in sorted(craft_dir.glob("*.yaml")):
                try:
                    rules.append(f"# 来自 {f.name}")
                    rules.append(f.read_text(encoding="utf-8")[:2000])
                    rules.append("")
                except Exception:
                    pass
            for f in sorted(craft_dir.glob("*.md")):
                try:
                    content = f.read_text(encoding="utf-8")
                    rules.append(f"# 来自 {f.name}")
                    rules.append(_extract_rules_from_md(content))
                    rules.append("")
                except Exception:
                    pass

    if not rules:
        rules.append(INLINE_IRON_RULES)

    return "\n".join(rules)


def compile_system_prompt(
    project_root: Path | None = None,
    include_rules: bool = True,
    include_style: bool = False,
) -> str:
    """编译完整的 System Prompt（铁律 + 风格 + 实体锁定）。"""
    parts = []

    parts.append("你是一位经验丰富的网文作者。请严格按照以下规则写作。\n")

    if include_rules:
        parts.append("## 写作铁律\n")
        parts.append(compile_iron_rules(project_root))
        parts.append("")

    if include_style and project_root:
        style_path = project_root / "src" / "story" / "author_intent.md"
        if style_path.exists():
            parts.append("## 作者意图\n")
            parts.append(style_path.read_text(encoding="utf-8")[:1000])
            parts.append("")

        focus_path = project_root / "src" / "story" / "current_focus.md"
        if focus_path.exists():
            parts.append("## 当前创作罗盘\n")
            parts.append(focus_path.read_text(encoding="utf-8")[:800])
            parts.append("")

    return "\n".join(parts)


def _extract_rules_from_md(content: str) -> str:
    """从 Markdown 文件中提取关键规则。"""
    lines = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("## ") or line.startswith("- ") or line.startswith("* "):
            lines.append(line)
            if len(lines) > 20:
                break
    return "\n".join(lines) if lines else content[:500]


def get_entity_dictionary(project_root: Path) -> dict[str, list[str]]:
    """从 src/ 提取实体字典（人物/地点/功法/物品）。"""
    entities: dict[str, list[str]] = {
        "characters": [],
        "locations": [],
        "techniques": [],
        "items": [],
    }

    chars_dir = project_root / "src" / "characters"
    if chars_dir.is_dir():
        for f in chars_dir.glob("*.md"):
            entities["characters"].append(f.stem)

    world_dir = project_root / "src" / "world"
    if world_dir.is_dir():
        for f in world_dir.glob("*.md"):
            entities["locations"].append(f.stem)

    return entities


def entity_lock_prompt(project_root: Path) -> str:
    """生成实体锁定 Prompt 片段。"""
    entities = get_entity_dictionary(project_root)

    if not any(entities.values()):
        return ""

    lines = ["## 实体锁定字典", "以下名词必须使用，严禁生造："]
    for category, items in entities.items():
        if items:
            lines.append(f"- {category}: {', '.join(items[:20])}")

    return "\n".join(lines)
