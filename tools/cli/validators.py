"""CLI 参数校验 — 前置条件检查与输入规范化。

所有参数校验逻辑集中在此模块，与 argparse 和业务逻辑解耦。
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger("tools.cli")


# ── 章节 ID ────────────────────────────────────────────────

def parse_chapter_no(chapter_id: str) -> int:
    """从 'ch_001' 中提取章节序号"""
    m = re.search(r"(\d+)", chapter_id)
    return int(m.group(1)) if m else 0


def validate_chapter_id(chapter_id: str) -> bool:
    """校验章节 ID 格式"""
    return bool(re.match(r"^ch_\d+$", chapter_id))


# ── 安全文件名 ─────────────────────────────────────────────

def safe_stem(value: str) -> str:
    """将用户输入规范化为安全文件名（不含路径成分）"""
    text = (value or "").strip()
    if any(x in text for x in ("/", "\\")) or ".." in text:
        return ""
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]", "", text)
    return text[:64]


# ── 端口 ───────────────────────────────────────────────────

def validate_port(port: int) -> bool:
    """校验端口号范围"""
    return 0 <= port <= 65535


# ── 模型配置 ───────────────────────────────────────────────

def validate_model_config() -> dict[str, str | None]:
    """检查模型环境变量配置，返回诊断信息"""
    model = (os.environ.get("LLM_MODEL") or "").strip()
    provider = (os.environ.get("LLM_PROVIDER") or "").strip()
    api_key = (os.environ.get("LLM_API_KEY") or "").strip()

    masked = "<缺失>"
    if api_key:
        masked = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"

    return {
        "provider": provider or None,
        "model": model or None,
        "api_key_masked": masked,
        "is_configured": bool(provider and model and api_key),
    }


# ── novel_id 解析 ──────────────────────────────────────────

def resolve_novel_id(project_root: Path, requested: str) -> str:
    """解析 novel_id：优先使用显式请求，否则从 config 读取"""
    if requested and requested != "current":
        return requested
    config = _load_novel_config(project_root) or {}
    return str(config.get("novel_id", "")).strip()


# ── 配置加载（内部） ───────────────────────────────────────

def _load_novel_config(project_root: Path) -> dict | None:
    """加载 novel_config.yaml"""
    config_path = project_root / "novel_config.yaml"
    if not config_path.exists():
        return None
    import yaml
    with config_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_novel_config(project_root: Path) -> dict | None:
    """加载 novel_config.yaml（公开接口）"""
    return _load_novel_config(project_root)
