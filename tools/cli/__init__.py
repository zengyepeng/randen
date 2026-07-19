"""Randen CLI — 命令行接口包。

模块结构:
    main.py       — 主入口 main()，创建解析器并分发命令
    commands.py   — 22 个 _add_*_command 函数（纯 argparse 注册）
    handlers.py   — 22 个 _handle_* 函数（委托给 NovelApplicationService）
    display.py    — 格式化输出工具（表格、面板、进度条、emoji）
    validators.py — 参数校验、前置条件检查

此 __init__.py 同时作为向后兼容入口，保留所有原有导出。
"""

import logging as _logging
from pathlib import Path  # noqa: F401 — 测试 monkeypatch 兼容

# ── 主入口 ────────────────────────────────────────────────
from tools.cli.main import main  # noqa: F401

# ── 日志器（测试 monkeypatch 兼容） ──────────────────────
logger = _logging.getLogger("tools.cli")

# ── 新式 handler 函数（通过别名保持旧名称） ──────────────
from tools.cli.handlers import (  # noqa: F401
    handle_init as _cmd_init,
    handle_setup as _cmd_setup,
    handle_goethe as _cmd_goethe,
    handle_dante as _cmd_dante,
    handle_sync as _cmd_sync,
    handle_write as _cmd_write,
    handle_multi_write as _cmd_multi_write,
    handle_review as _cmd_review,
    handle_context as _cmd_context,
    handle_assemble as _cmd_assemble,
    handle_style as _cmd_style,
    handle_setting as _cmd_setting,
    handle_source as _cmd_source,
    handle_radar as _cmd_radar,
    handle_status as _cmd_status,
    handle_focus as _cmd_focus,
    handle_import as _cmd_import,
    handle_export as _cmd_export,
    handle_desk as _cmd_desk,
    handle_studio as _cmd_studio,
    handle_doctor as _cmd_doctor,
    handle_agent as _cmd_agent,
)

# ── 格式化 / 同步工具 ─────────────────────────────────────
from tools.cli.display import (  # noqa: F401
    build_sync_actions as _build_sync_actions,
    build_sync_suggestions as _build_sync_suggestions,
    print_sync_status as _print_sync_status,
    print_desk as _print_desk,
    print_status as _print_status,
    print_market_radar as _print_market_radar,
    show_success as _show_success,
    show_error as _show_error,
)

# ── 校验工具 ──────────────────────────────────────────────
from tools.cli.validators import (  # noqa: F401
    parse_chapter_no as _parse_chapter_no,
    safe_stem as _safe_stem,
    validate_chapter_id as _validate_chapter_id,
    validate_model_config as _validate_model_config,
    validate_port as _validate_port,
    resolve_novel_id as _resolve_novel_id,
    load_novel_config as _load_config,
)

# ── exec 委托（兼容入口） ────────────────────────────────
from tools.agent.tool_runtime import build_tool_executors as _build_tool_executors  # noqa: F401


def _exec_get_status(project_root, args=None):
    return _build_tool_executors(project_root)["get_status"](args or {})


def _exec_get_context(project_root, args):
    return _build_tool_executors(project_root)["get_context"](args)


def _exec_list_chapters(project_root):
    return _build_tool_executors(project_root)["list_chapters"]({})


def _exec_create_outline(project_root, args):
    return _build_tool_executors(project_root)["create_outline"](args)


def _exec_create_character(project_root, args):
    return _build_tool_executors(project_root)["create_character"](args)


def _exec_get_truth_files(project_root):
    return _build_tool_executors(project_root)["get_truth_files"]({})


def _exec_update_truth_file(project_root, args):
    return _build_tool_executors(project_root)["update_truth_file"](args)


def _exec_create_foreshadowing(project_root, args):
    return _build_tool_executors(project_root)["create_foreshadowing"](args)


def _exec_list_foreshadowing(project_root, args):
    return _build_tool_executors(project_root)["list_foreshadowing"](args)


def _exec_update_foreshadowing(project_root, args):
    return _build_tool_executors(project_root)["update_foreshadowing"](args)


def _exec_validate_foreshadowing(project_root, args):
    return _build_tool_executors(project_root)["validate_foreshadowing"](args)


def _exec_query_world(project_root, args):
    return _build_tool_executors(project_root)["query_world"](args)


def _exec_get_world_relations(project_root, args):
    return _build_tool_executors(project_root)["get_world_relations"](args)


def _exec_validate_truth(project_root, args):
    return _build_tool_executors(project_root)["validate_truth"](args)


def _exec_extract_dialogue_fingerprint(project_root, args):
    return _build_tool_executors(project_root)["extract_dialogue_fingerprint"](args)


def _exec_validate_post_write(project_root, args):
    return _build_tool_executors(project_root)["validate_post_write"](args)


def _exec_get_workflow_status(project_root, args):
    return _build_tool_executors(project_root)["get_workflow_status"](args)


def _exec_start_workflow(project_root, args):
    return _build_tool_executors(project_root)["start_workflow"](args)


def _exec_advance_workflow(project_root, args):
    return _build_tool_executors(project_root)["advance_workflow"](args)


def _exec_chunk_text(project_root, args):
    return _build_tool_executors(project_root)["chunk_text"](args)


def _exec_compress_section(project_root, args):
    return _build_tool_executors(project_root)["compress_section"](args)


# ── 章节管道兼容入口 ─────────────────────────────────────

def _build_writer_context_payload(*, context, truth, context_packet, guidance, target_words):
    from tools.chapter_pipeline import build_writer_payload
    return build_writer_payload(context=context, truth=truth,
                                packet=context_packet, guidance=guidance,
                                target_words=target_words)


def _build_reviewer_context_payload(context_packet):
    from tools.chapter_pipeline import build_review_payload
    return build_review_payload(context_packet)


def _exec_write_chapter(project_root, args):
    from tools.chapter_pipeline import execute_write_chapter
    return execute_write_chapter(project_root, args)


def _exec_review_chapter(project_root, args):
    from tools.chapter_pipeline import execute_review_chapter
    return execute_review_chapter(project_root, args)


# ── 章节 I/O ──────────────────────────────────────────────

def _load_chapter(project_root, novel_id, chapter_id):
    from tools.chapter_pipeline import load_chapter
    return load_chapter(project_root, novel_id, chapter_id)


def _save_chapter(project_root, novel_id, chapter_id, title, content):
    from tools.chapter_pipeline import save_chapter
    return save_chapter(project_root, novel_id, chapter_id, title, content)


# ── 同步工具 ──────────────────────────────────────────────

def _collect_sync_status(project_root, novel_id):
    from tools.source_sync import collect_sync_status
    return collect_sync_status(project_root, novel_id)


def _run_sync(project_root, novel_id):
    from tools.source_sync import run_sync as _run
    _run(project_root, novel_id)


# ── Source Pack 工具 ──────────────────────────────────────

def _extract_source_pack(project_root, novel_id, source_id, source_file, *, focus, chunk_size=30000):
    from tools.source_pack import SourcePackService
    return SourcePackService(project_root, novel_id).extract(
        source_id, source_file, focus=focus, chunk_size=chunk_size)


def _refresh_source_pack_documents(project_root, novel_id, source_id):
    from tools.source_pack import SourcePackService
    SourcePackService(project_root, novel_id).refresh_documents(source_id)


def _render_source_review(project_root, novel_id, source_id):
    from tools.source_pack import SourcePackService
    return SourcePackService(project_root, novel_id).render_review(source_id)


def _promote_source_style(project_root, novel_id, source_id):
    from tools.source_pack import SourcePackService
    SourcePackService(project_root, novel_id).promote(source_id, "style")


def _promote_source_setting(project_root, novel_id, source_id):
    from tools.source_pack import SourcePackService
    SourcePackService(project_root, novel_id).promote(source_id, "setting")


def _promote_source_world(project_root, novel_id, source_id):
    from tools.source_pack import SourcePackService
    SourcePackService(project_root, novel_id).promote(source_id, "world")


# ── Truth 工具 ────────────────────────────────────────────

def _collect_truth_updates(state_updates):
    from tools.context_schema import normalize_truth_file_key
    if not isinstance(state_updates, dict):
        return {}
    file_map = {"current_state": "current_state", "ledger": "ledger", "relationships": "relationships"}
    out: dict[str, str] = {}
    for key, value in state_updates.items():
        if not isinstance(value, str) or not value.strip():
            continue
        canonical = normalize_truth_file_key(key)
        attr = file_map.get(canonical)
        if attr:
            out[attr] = value
    return out


# ── 文件/路径工具 ────────────────────────────────────────

def _get_test_output_dir(project_root, novel_id, category):
    return project_root / "data" / "novels" / novel_id / "data" / "test_outputs" / category


def _get_current_arc(project_root):
    config = _load_config(project_root) or {}
    return config.get("current_arc") or "arc_001"


def _manuscript_dir(project_root, novel_id):
    return project_root / "data" / "novels" / novel_id / "data" / "manuscript"


def _chapter_file_path(project_root, novel_id, chapter_id):
    config = _load_config(project_root) or {}
    current_arc = config.get("current_arc", "arc_001")
    return project_root / "data" / "novels" / novel_id / "data" / "manuscript" / current_arc / f"{chapter_id}.md"


def _atomic_write_bytes(path, content):
    import os, tempfile
    with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent,
                                     prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        handle.write(content); handle.flush(); os.fsync(handle.fileno())
        temp_path = type(path)(handle.name)
    temp_path.replace(path)


def _get_next_chapter(project_root, novel_id):
    chapter_ids = _list_chapter_ids(project_root, novel_id)
    if not chapter_ids: return "ch_001"
    latest = max(_parse_chapter_no(chid) for chid in chapter_ids)
    return f"ch_{latest + 1:03d}"


def _get_latest_chapter(project_root, novel_id):
    chapter_ids = _list_chapter_ids(project_root, novel_id)
    if not chapter_ids: return "ch_001"
    return max(chapter_ids, key=_parse_chapter_no)


def _list_chapter_ids(project_root, novel_id):
    import re as _re
    from pathlib import Path as _Path
    manuscript_root = _Path(project_root) / "data" / "novels" / novel_id / "data" / "manuscript"
    if not manuscript_root.exists(): return []
    chapter_ids: set[str] = set()
    for path in manuscript_root.glob("**/ch_*.md"):
        stem = path.stem
        if _re.match(r"^ch_\d+$", stem): chapter_ids.add(stem)
    return sorted(chapter_ids, key=_parse_chapter_no)


# ── 层构建兼容入口 ───────────────────────────────────────

def build_cli_tool_executors(project_root):
    from tools.agent.tool_runtime import build_tool_executors
    return build_tool_executors(project_root)


def build_dante_tool_layers(project_root):
    from tools.agent.tool_layers import build_dante_tool_layers as _build
    return _build(project_root)


def build_goethe_tool_layers(project_root, novel_id=None):
    from tools.agent.tool_layers import build_goethe_tool_layers as _build
    return _build(project_root, novel_id)


__all__ = ["main", "logger"]
