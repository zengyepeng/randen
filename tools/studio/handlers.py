"""Randen Studio HTTP 请求处理函数——所有 API 端点业务逻辑。"""

from __future__ import annotations

import os
import re
import tempfile
from http import HTTPStatus
from pathlib import Path
from typing import Any

from .app import StudioApplication, StudioError


# ═══════════════════════════════════════════════════════════════
# GET 端点处理器
# ═══════════════════════════════════════════════════════════════

def handle_health(app: StudioApplication, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """健康检查。"""
    return {"ok": True}


def handle_workspace(app: StudioApplication, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """返回完整工作区快照。"""
    return app.workspace()


def handle_continuity(
    app: StudioApplication, params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """返回连续性（伏笔 + 时间线）信息。"""
    app.require_project()
    return app.continuity()


def handle_context(
    app: StudioApplication, params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """返回章节上下文预览。"""
    app.require_project()
    chapter_id = (params or {}).get("chapter", "next")
    return app.context_preview(str(chapter_id))


def handle_document_read(
    app: StudioApplication, params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """读取单个文档。"""
    app.require_project()
    path = (params or {}).get("path", "")
    return app.read_document(str(path))


def handle_export(
    app: StudioApplication, params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """导出全书为文件下载（返回 _export 标记字典）。"""
    app.require_project()
    format_name = str((params or {}).get("format", "md"))
    filename, content, mime = app.export_download(format_name)
    return {"_export": True, "filename": filename, "content": content, "mime": mime}


# ═══════════════════════════════════════════════════════════════
# POST 端点处理器
# ═══════════════════════════════════════════════════════════════

def handle_project_init(
    app: StudioApplication, body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """初始化小说项目。"""
    return app.initialize_project(body or {})


def handle_focus(
    app: StudioApplication, body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """更新创作焦点。"""
    return app.update_focus(body or {})


def handle_model(
    app: StudioApplication, body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """配置模型参数。"""
    return app.configure_model(body or {})


def handle_write(
    app: StudioApplication, body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """写入下一章。"""
    return _ops_write_next_chapter(app, body or {})


def handle_review(
    app: StudioApplication, body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """审查指定章节。"""
    return _ops_review_chapter(app, body or {})


def handle_sync(
    app: StudioApplication, body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """同步项目数据。"""
    return _ops_sync_project(app)


def handle_document_create(
    app: StudioApplication, body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建新文档（角色/世界/故事）。"""
    return app.create_document(body or {})


def handle_import(
    app: StudioApplication, body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """导入外部文本为章节。"""
    return _ops_import_text(app, body or {})


def handle_foreshadowing(
    app: StudioApplication, body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """管理伏笔系统。"""
    return _ops_manage_foreshadowing(app, body or {})


def handle_chat(
    app: StudioApplication, body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """AI 聊天对话。"""
    return _ops_chat_turn(app, body or {})


def handle_source(
    app: StudioApplication, body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """来源材料操作（抽取/审查/推广/合成）。"""
    return _ops_source_action(app, body or {})


# ═══════════════════════════════════════════════════════════════
# PUT 端点处理器
# ═══════════════════════════════════════════════════════════════

def handle_document_write(
    app: StudioApplication, body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """保存文档内容。"""
    payload = body or {}
    return app.write_document(
        str(payload.get("path") or ""),
        str(payload.get("content") or ""),
        payload.get("version") if isinstance(payload.get("version"), (str, int)) else None,
        force=bool(payload.get("force")),
    )


# ═══════════════════════════════════════════════════════════════
# 重型操作（app.py 委托，供 routes/server 共用）
# ═══════════════════════════════════════════════════════════════

def _ops_manage_foreshadowing(
    app: StudioApplication, payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        result = app.service().manage_foreshadowing(payload)
    except Exception as exc:
        raise app._translate_service_error(exc) from exc  # noqa: SLF001
    return {**result, "workspace": app.workspace()}


def _ops_write_next_chapter(
    app: StudioApplication, payload: dict[str, Any],
) -> dict[str, Any]:
    if not os.environ.get("LLM_API_KEY", "").strip():
        raise StudioError("未配置 LLM_API_KEY", HTTPStatus.PRECONDITION_FAILED)
    try:
        target_words = int(payload.get("target_words") or 3000)
    except (TypeError, ValueError) as exc:
        raise StudioError("目标字数必须是整数") from exc
    if not 200 <= target_words <= 12000:
        raise StudioError("目标字数必须在 200 到 12000 之间")
    guidance = str(payload.get("guidance") or "").strip()
    try:
        result = app.service().write_chapter({
            "chapter_id": "next", "guidance": guidance,
            "target_words": target_words,
            "temperature": float(payload.get("temperature") or 0.7),
        })
    except Exception as exc:
        raise app._translate_service_error(exc) from exc  # noqa: SLF001
    return {"result": result, "workspace": app.workspace()}


def _ops_review_chapter(
    app: StudioApplication, payload: dict[str, Any],
) -> dict[str, Any]:
    if not os.environ.get("LLM_API_KEY", "").strip():
        raise StudioError("未配置 LLM_API_KEY", HTTPStatus.PRECONDITION_FAILED)
    relative_path = str(payload.get("path") or "")
    path = app._resolve_document(relative_path, write=False)  # noqa: SLF001
    manuscript_root = (app.novel_root / "data" / "manuscript").resolve()
    if manuscript_root not in path.parents or not re.fullmatch(r"ch_\d+", path.stem):
        raise StudioError("只能审查正文章节")
    try:
        result = app.service().review_chapter(path.stem)
    except Exception as exc:
        raise app._translate_service_error(exc) from exc  # noqa: SLF001
    return {"result": result, "workspace": app.workspace()}


def _ops_sync_project(app: StudioApplication) -> dict[str, Any]:
    try:
        result = app.service().sync()
    except Exception as exc:
        raise app._translate_service_error(exc) from exc  # noqa: SLF001
    return {**result, "workspace": app.workspace()}


def _ops_import_text(
    app: StudioApplication, payload: dict[str, Any],
) -> dict[str, Any]:
    filename = str(payload.get("filename") or "import.md").strip()
    content = str(payload.get("content") or "")
    if not content.strip():
        raise StudioError("导入内容不能为空")
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".md", ".markdown"}:
        raise StudioError("当前仅支持 TXT 和 Markdown 导入")
    arc_id = str(payload.get("arc_id") or app.config.get("current_arc") or "arc_001")
    if not re.fullmatch(r"arc_\d+", arc_id):
        raise StudioError("篇 ID 必须形如 arc_001")
    start_number = payload.get("start_number")
    if start_number in {None, ""}:
        start = None
    else:
        try:
            start = int(start_number)
        except (TypeError, ValueError) as exc:
            raise StudioError("起始章节必须是整数") from exc
    with app.write_lock, tempfile.TemporaryDirectory(prefix="randen-import-") as temp_dir:
        source = Path(temp_dir) / f"source{suffix}"
        source.write_text(content, encoding="utf-8")
        try:
            result = app.service().import_book(
                source, arc_id=arc_id, start_number=start,
                force=bool(payload.get("force")))
        except Exception as exc:
            raise app._translate_service_error(exc) from exc  # noqa: SLF001
    return {"imported": result["imported"], "workspace": app.workspace()}


def _ops_chat_turn(
    app: StudioApplication, payload: dict[str, Any],
) -> dict[str, Any]:
    if not os.environ.get("LLM_API_KEY", "").strip():
        raise StudioError("未配置 LLM_API_KEY", HTTPStatus.PRECONDITION_FAILED)
    agent_name = str(payload.get("agent") or "dante").strip().lower()
    message = str(payload.get("message") or "").strip()
    if agent_name not in {"goethe", "dante"}:
        raise StudioError("Agent 仅支持 goethe 或 dante")
    if not message or len(message) > 12000:
        raise StudioError("消息不能为空且不能超过 12000 字")
    if not app.write_lock.acquire(blocking=False):
        raise StudioError("已有 AI 任务正在运行", HTTPStatus.CONFLICT)
    try:
        if app.chat_executor is not None:
            result = app.chat_executor(
                app.project_root, app.novel_id, agent_name, message)
        elif agent_name == "goethe":
            from tools.goethe import GoetheChatAgent  # noqa: PLC0415
            response = GoetheChatAgent(
                app.project_root, app.novel_id).respond(message)
            result = {"content": response}
        else:
            from tools.agent.dante import DanteChatAgent  # noqa: PLC0415
            from tools.agent.tool_layers import build_dante_tool_layers  # noqa: PLC0415
            layers = build_dante_tool_layers(app.project_root)
            agent = DanteChatAgent(
                app.project_root, app.novel_id,
                tool_executors=layers.get("direct_tool_executors", {}),
                action_executors=layers.get("action_tool_executors", {}),
            )
            result = {"content": agent.respond(message)}
    finally:
        app.write_lock.release()
    if result.get("error"):
        raise StudioError(str(result["error"]), HTTPStatus.BAD_GATEWAY)
    return {
        "agent": agent_name,
        "content": str(result.get("content") or ""),
        "workspace": app.workspace(),
    }


def _ops_source_action(
    app: StudioApplication, payload: dict[str, Any],
) -> dict[str, Any]:
    action = str(payload.get("action") or "").strip()
    source_id = str(payload.get("source_id") or "").strip()
    try:
        if action == "extract":
            if not os.environ.get("LLM_API_KEY", "").strip():
                raise StudioError("未配置 LLM_API_KEY", HTTPStatus.PRECONDITION_FAILED)
            text = str(payload.get("content") or "")
            if not text.strip():
                raise StudioError("来源文本不能为空")
            with tempfile.TemporaryDirectory(prefix="randen-source-") as temp_dir:
                source = Path(temp_dir) / "source.txt"
                source.write_text(text, encoding="utf-8")
                result = app.service().extract_source(
                    source_id=source_id, source_file=source,
                    focus=str(payload.get("focus") or "style"))
        elif action == "review":
            result = app.service().review_source(source_id)
        elif action == "promote":
            result = app.service().promote_source(
                source_id, str(payload.get("target") or "all"))
        elif action == "synthesize":
            result = app.service().synthesize_style(source_id)
        else:
            raise StudioError("未知来源操作")
    except Exception as exc:
        raise app._translate_service_error(exc) from exc  # noqa: SLF001
    return {"result": result, "workspace": app.workspace()}


def _ops_export_download(
    app: StudioApplication, format_name: str,
) -> tuple[str, bytes, str]:
    if format_name not in {"md", "txt"}:
        raise StudioError("导出格式仅支持 md 或 txt")
    title = str(app.config.get("title") or app.novel_id)
    with tempfile.TemporaryDirectory(prefix="randen-export-") as temp_dir:
        output = Path(temp_dir) / f"{app.novel_id}.{format_name}"
        try:
            app.service().export_book(output, format_name=format_name, title=title)
        except Exception as exc:
            raise app._translate_service_error(exc) from exc  # noqa: SLF001
        content = output.read_bytes()
    mime = "text/markdown; charset=utf-8" if format_name == "md" else "text/plain; charset=utf-8"
    return f"{app.novel_id}.{format_name}", content, mime

# ── 创作引擎 ───────────────────────────────────────────────

def handle_market(app, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """扫榜分析"""
    from tools.creation_engine import analyze_market
    platform = (params or {}).get("platform", "默认")
    return {"markets": analyze_market(platform)}


def handle_dissect(app, params: dict[str, Any]) -> dict[str, Any]:
    """拆书分析"""
    from tools.creation_engine import dissect_book
    text = str(params.get("text") or "")
    title = str(params.get("title") or "未命名作品")
    if not text.strip():
        raise RuntimeError("请提供待拆解的正文内容")
    return dissect_book(text, title)


def handle_idea(app, params: dict[str, Any]) -> dict[str, Any]:
    """脑洞完善"""
    from tools.creation_engine import refine_idea
    return refine_idea(
        premise=str(params.get("premise") or ""),
        genre=str(params.get("genre") or ""),
        golden_finger_idea=str(params.get("golden_finger") or ""),
    )


def handle_opening(app, params: dict[str, Any]) -> dict[str, Any]:
    """开篇诊断"""
    from tools.creation_engine import diagnose_opening
    text = str(params.get("text") or "")
    if len(text) < 50:
        raise RuntimeError("正文太短，请至少提供一段开篇（建议200字以上）")
    return diagnose_opening(text)


def handle_faq(app, _params: dict[str, Any] | None = None) -> dict[str, Any]:
    """新人FAQ"""
    from tools.creation_engine import get_faq_for_newcomer
    return {"faq": get_faq_for_newcomer()}
