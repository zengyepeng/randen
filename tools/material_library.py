"""燃灯 素材库 — 每本小说独立的创作素材管理系统

两种用法:
1. 背景生成模式: 素材 → 世界观/人物/情节设定生成
2. 写作注入模式: 素材 → 章节写作上下文，在写正文时自动引用
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import yaml
import time


MATERIAL_CATEGORIES = {
    "character": {"label": "人物素材", "icon": "👤", "desc": "角色灵感、性格碎片、外貌参考、人物关系想法"},
    "world": {"label": "世界素材", "icon": "🌍", "desc": "世界观碎片、地理构想、历史事件、规则设定"},
    "plot": {"label": "情节素材", "icon": "📜", "desc": "桥段想法、冲突点子、反转设计、场景草稿"},
    "reference": {"label": "参考素材", "icon": "📖", "desc": "对标作品笔记、拆书精华、可借鉴写法"},
    "dialogue": {"label": "对话素材", "icon": "💬", "desc": "有意思的对话片段、口头禅、经典对白"},
    "setting": {"label": "场景素材", "icon": "🎬", "desc": "场景描写、环境氛围、地点设定"},
    "research": {"label": "考据素材", "icon": "🔬", "desc": "历史考据、科学知识、行业细节"},
    "note": {"label": "随手记", "icon": "📝", "desc": "灵光一闪、待办想法、任何碎片"},
}


def get_material_dir(project_root: str, novel_id: str) -> Path:
    return Path(project_root) / "data" / "novels" / novel_id / "materials"


def list_materials(project_root: str, novel_id: str, category: str = "") -> list[dict]:
    """列出素材"""
    root = get_material_dir(project_root, novel_id)
    if not root.exists():
        return []

    materials = []
    for cat_dir in sorted(root.iterdir()):
        if not cat_dir.is_dir():
            continue
        cat = cat_dir.name
        if category and cat != category:
            continue
        for f in sorted(cat_dir.glob("*.yaml")):
            try:
                with f.open(encoding="utf-8") as fh:
                    data = yaml.safe_load(fh) or {}
                materials.append({
                    "id": f.stem,
                    "category": cat,
                    "category_label": MATERIAL_CATEGORIES.get(cat, {}).get("label", cat),
                    "title": data.get("title", f.stem),
                    "content": data.get("content", ""),
                    "tags": data.get("tags", []),
                    "created": data.get("created", ""),
                    "usage": data.get("usage", "both"),  # background / writing / both
                })
            except Exception:
                pass
    return sorted(materials, key=lambda x: (x["category"], x["id"]))


def create_material(project_root: str, novel_id: str, category: str,
                    title: str, content: str, tags: list[str] | None = None,
                    usage: str = "both") -> dict:
    """创建素材"""
    if category not in MATERIAL_CATEGORIES:
        return {"error": f"未知分类: {category}"}

    root = get_material_dir(project_root, novel_id)
    cat_dir = root / category
    cat_dir.mkdir(parents=True, exist_ok=True)

    ts = time.strftime("%Y%m%d_%H%M%S")
    mat_id = f"{category}_{ts}"

    data = {
        "title": title or mat_id,
        "category": category,
        "content": content,
        "tags": tags or [],
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "usage": usage,
    }

    filepath = cat_dir / f"{mat_id}.yaml"
    filepath.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False), encoding="utf-8")

    return {"ok": True, "id": mat_id, "file": str(filepath.relative_to(root)), "data": data}


def update_material(project_root: str, novel_id: str, material_id: str,
                    updates: dict[str, Any]) -> dict:
    """更新素材"""
    root = get_material_dir(project_root, novel_id)
    # 从 id 推断分类
    for cat_dir in sorted(root.iterdir()):
        if not cat_dir.is_dir():
            continue
        fpath = cat_dir / f"{material_id}.yaml"
        if fpath.exists():
            with fpath.open(encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            for k, v in updates.items():
                if v is not None:
                    data[k] = v
            data["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            fpath.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False), encoding="utf-8")
            return {"ok": True, "id": material_id, "data": data}
    return {"error": f"素材不存在: {material_id}"}


def delete_material(project_root: str, novel_id: str, material_id: str) -> dict:
    """删除素材"""
    root = get_material_dir(project_root, novel_id)
    for cat_dir in sorted(root.iterdir()):
        if not cat_dir.is_dir():
            continue
        fpath = cat_dir / f"{material_id}.yaml"
        if fpath.exists():
            fpath.unlink()
            # 清理空目录
            if not list(cat_dir.iterdir()):
                cat_dir.rmdir()
            return {"ok": True, "id": material_id}
    return {"error": f"素材不存在: {material_id}"}


def get_material(project_root: str, novel_id: str, material_id: str) -> dict:
    """读取单个素材"""
    root = get_material_dir(project_root, novel_id)
    for cat_dir in sorted(root.iterdir()):
        if not cat_dir.is_dir():
            continue
        fpath = cat_dir / f"{material_id}.yaml"
        if fpath.exists():
            with fpath.open(encoding="utf-8") as f:
                return {"ok": True, "id": material_id, "data": yaml.safe_load(f) or {}}
    return {"error": f"素材不存在: {material_id}"}


def build_material_context(project_root: str, novel_id: str, usage_mode: str = "both") -> str:
    """构建素材上下文 — 用于注入写作流程

    Args:
        usage_mode: "background"(只取背景素材) / "writing"(只取写作素材) / "both"(全部)
    """
    materials = list_materials(project_root, novel_id)
    if not materials:
        return ""

    relevant = [m for m in materials if usage_mode == "both" or m.get("usage") == usage_mode or m.get("usage") == "both"]

    if not relevant:
        return ""

    lines = ["## 📚 创作素材库\n"]
    current_cat = ""
    for m in relevant:
        if m["category_label"] != current_cat:
            current_cat = m["category_label"]
            lines.append(f"\n### {current_cat}")
        title = m["title"]
        content = m["content"][:200]  # 截取前200字避免上下文过长
        tags = " · ".join(m.get("tags", [])[:3])
        tag_str = f" [{tags}]" if tags else ""
        lines.append(f"- **{title}**{tag_str}: {content}")
        if len(m["content"]) > 200:
            lines.append("  *(更多内容见素材库)*")

    return "\n".join(lines)


def get_material_stats(project_root: str, novel_id: str) -> dict:
    """素材库统计"""
    materials = list_materials(project_root, novel_id)
    by_cat = {}
    for m in materials:
        cat = m["category"]
        by_cat[cat] = by_cat.get(cat, 0) + 1
    return {
        "total": len(materials),
        "by_category": by_cat,
        "categories": [{"key": k, "label": v["label"], "icon": v["icon"], "count": by_cat.get(k, 0)}
                       for k, v in MATERIAL_CATEGORIES.items()],
    }
