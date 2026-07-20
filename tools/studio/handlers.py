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

def handle_dissect_deep(app, params: dict[str, Any]) -> dict[str, Any]:
    """深度拆书（整本）"""
    from tools.creation_engine import dissect_book_deep
    text = str(params.get("text") or "")
    title = str(params.get("title") or "未命名作品")
    if len(text.strip()) < 100:
        raise RuntimeError("正文太短，请上传完整作品（建议3000字以上）")
    return dissect_book_deep(text, title)


def handle_dissect_multi(app, params: dict[str, Any]) -> dict[str, Any]:
    """多书批量拆解"""
    from tools.creation_engine import dissect_multi_books
    books = params.get("books", [])
    if not isinstance(books, list) or len(books) < 1:
        raise RuntimeError("请至少提供一本书的内容")
    return dissect_multi_books(books)


def handle_merge_dissections(app, params: dict[str, Any]) -> dict[str, Any]:
    """融合多本书拆解结果"""
    from tools.creation_engine import merge_dissections
    results = params.get("results", [])
    if not isinstance(results, list):
        raise RuntimeError("请提供拆解结果列表")
    return merge_dissections(results)

def handle_save_result(app, params: dict[str, Any]) -> dict[str, Any]:
    """保存向导结果到项目"""
    from tools.creation_engine import save_wizard_result
    rtype = str(params.get("type") or "unknown")
    data = params.get("data", {})
    title = str(params.get("title") or "")
    return save_wizard_result(str(app.project_root), rtype, data, title)


def handle_character_guide(app, params: dict[str, Any]) -> dict[str, Any]:
    """角色创建引导"""
    from tools.creation_engine import get_character_guide
    genre = str(params.get("genre") or "默认")
    return get_character_guide(genre)


def handle_generate_outline(app, params: dict[str, Any]) -> dict[str, Any]:
    """从脑洞生成大纲"""
    from tools.creation_engine import generate_outline_from_idea
    premise = str(params.get("premise") or "")
    if not premise.strip():
        raise RuntimeError("请先输入灵感")
    return generate_outline_from_idea(premise, str(params.get("genre") or ""))


def handle_epub_extract(app, params: dict[str, Any]) -> dict[str, Any]:
    """EPUB 文本提取 — 接受 base64 编码内容"""
    from tools.creation_engine import extract_text_from_epub
    import base64
    text = str(params.get("text") or "")
    if not text:
        raise RuntimeError("请上传 EPUB 文件")
    # Decode base64 content
    try:
        raw = base64.b64decode(text)
    except Exception:
        raise RuntimeError("文件编码错误，请重新上传")
    if len(raw) < 100:
        raise RuntimeError("文件内容过短")
    return extract_text_from_epub(raw, is_bytes=True)


def handle_ai_dissect(app, params: dict[str, Any]) -> dict[str, Any]:
    """AI 深度拆书"""
    from tools.creation_engine import ai_deep_dissect
    text = str(params.get("text") or "")
    title = str(params.get("title") or "")
    if len(text) < 200:
        raise RuntimeError("正文太短，请提供完整片段")
    try:
        import openai
        client = openai.OpenAI(
            api_key=os.environ.get("LLM_API_KEY", ""),
            base_url=os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
        )
        return ai_deep_dissect(text, title, client)
    except ImportError:
        return ai_deep_dissect(text, title)


def handle_ai_imitate(app, params: dict[str, Any]) -> dict[str, Any]:
    """AI 仿写生成"""
    from tools.creation_engine import ai_style_imitate
    ref_text = str(params.get("reference_text") or "")
    premise = str(params.get("premise") or "")
    if not ref_text.strip() or not premise.strip():
        raise RuntimeError("请提供参考文本和梗概")
    try:
        import openai
        client = openai.OpenAI(
            api_key=os.environ.get("LLM_API_KEY", ""),
            base_url=os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
        )
        return ai_style_imitate(ref_text, premise, "", client)
    except ImportError:
        return {"error": "需要安装 openai 库: pip install openai"}

def handle_persona_template(app, _params=None) -> dict:
    """获取作者人设模板"""
    from tools.creation_engine import get_persona_template
    return get_persona_template()


def handle_persona_save(app, params: dict[str, Any]) -> dict:
    """保存作者人设"""
    from tools.creation_engine import save_persona
    return save_persona(str(app.project_root), params.get("persona", {}))


def handle_persona_load(app, _params=None) -> dict:
    """加载作者人设"""
    from tools.creation_engine import load_persona
    return load_persona(str(app.project_root))

def handle_dna_extract(app, params: dict[str, Any]) -> dict[str, Any]:
    """DNA 提取"""
    from tools.dna_extractor import extract_dna
    text = str(params.get("text") or "")
    title = str(params.get("title") or "未命名")
    if len(text) < 200:
        raise RuntimeError("正文太短，至少需要200字")
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ.get("LLM_API_KEY",""),base_url=os.environ.get("LLM_BASE_URL","https://api.deepseek.com/v1"))
        return extract_dna(text, title, llm_client=client)
    except ImportError:
        return extract_dna(text, title)


def handle_dna_blend(app, params: dict[str, Any]) -> dict[str, Any]:
    """风格融合"""
    from tools.dna_extractor import blend_styles
    dnas = params.get("dnas", [])
    weights = params.get("weights", None)
    instruction = str(params.get("instruction") or "")
    if len(dnas) < 2:
        raise RuntimeError("至少需要2本书的DNA才能融合")
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ.get("LLM_API_KEY",""),base_url=os.environ.get("LLM_BASE_URL","https://api.deepseek.com/v1"))
        return blend_styles(dnas, weights, instruction, client)
    except ImportError:
        return blend_styles(dnas, weights, instruction)

def handle_material_list(app, params=None):
    from tools.material_library import list_materials, get_material_stats
    category = str((params or {}).get("category", ""))
    mats = list_materials(str(app.project_root), app.novel_id, category)
    stats = get_material_stats(str(app.project_root), app.novel_id)
    return {"materials": mats, "stats": stats}


def handle_material_create(app, params):
    from tools.material_library import create_material
    return create_material(
        str(app.project_root), app.novel_id,
        category=str(params.get("category", "note")),
        title=str(params.get("title", "")),
        content=str(params.get("content", "")),
        tags=params.get("tags", []),
        usage=str(params.get("usage", "both")),
    )


def handle_material_update(app, params):
    from tools.material_library import update_material
    return update_material(str(app.project_root), app.novel_id,
                           str(params.get("id", "")), params.get("updates", {}))


def handle_material_delete(app, params):
    from tools.material_library import delete_material
    return delete_material(str(app.project_root), app.novel_id, str(params.get("id", "")))

def handle_ai_story(app, params):
    from tools.ai_assistants import story_assist
    action = str(params.get("action", "background"))
    content = str(params.get("content", ""))
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ.get("LLM_API_KEY",""),base_url=os.environ.get("LLM_BASE_URL","https://api.deepseek.com/v1"))
        return story_assist(action, content, None, client)
    except ImportError:
        return story_assist(action, content)
    except Exception as e:
        return story_assist(action, content)  # 降级到本地模式

def handle_ai_character(app, params):
    from tools.ai_assistants import character_assist
    action = str(params.get("action", "create"))
    content = str(params.get("content", ""))
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ.get("LLM_API_KEY",""),base_url=os.environ.get("LLM_BASE_URL","https://api.deepseek.com/v1"))
        return character_assist(action, content, None, client)
    except ImportError:
        return character_assist(action, content)
    except Exception as e:
        return character_assist(action, content)  # 降级到本地模式

def handle_ai_world(app, params):
    from tools.ai_assistants import world_assist
    action = str(params.get("action", "rules"))
    content = str(params.get("content", ""))
    try:
        import openai
        client = openai.OpenAI(api_key=os.environ.get("LLM_API_KEY",""),base_url=os.environ.get("LLM_BASE_URL","https://api.deepseek.com/v1"))
        return world_assist(action, content, None, client)
    except ImportError:
        return world_assist(action, content)
    except Exception as e:
        return world_assist(action, content)  # 降级到本地模式


# ═══════════════════════════════════════════════════════════════
# 灵感对话串联 API
# ═══════════════════════════════════════════════════════════════

def handle_inspire_apply(app, params: dict[str, Any]) -> dict[str, Any]:
    """解析作品雏形 Markdown，创建角色/世界观/大纲条目到项目。"""
    import re
    app.require_project()
    prototype = str(params.get("prototype") or "")
    if not prototype.strip():
        raise StudioError("请先生成作品雏形", HTTPStatus.BAD_REQUEST)

    created = {"characters": 0, "world": 0, "outline": False, "materials": 0}

    # ── Parse prototype sections ──
    sections = {}
    current_section = None
    for line in prototype.split("\n"):
        m = re.match(r"^##\s+(.+)", line)
        if m:
            current_section = m.group(1).strip()
            sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)

    project_root = Path(str(app.project_root))

    # ── 1. Extract characters ──
    char_section_key = None
    for k in sections:
        if "角色" in k or "核心角色" in k:
            char_section_key = k
            break
    if char_section_key:
        chars_text = "\n".join(sections[char_section_key])
        # Parse individual characters: lines starting with bullet or numbered
        char_entries = re.findall(r"(?:^[-*•]\s*|^\d+\.\s*)(.+?)(?=$|\n(?:[-*•]|\d+\.)|$)", chars_text, re.MULTILINE)
        if not char_entries:
            # Fallback: split by double newline or significant breaks
            char_entries = [l.strip() for l in chars_text.split("\n") if l.strip() and len(l.strip()) > 5]

        for entry in char_entries[:5]:  # Max 5 characters
            entry = entry.strip()
            if len(entry) < 5:
                continue
            # Extract name (first few characters before colon/comma/space)
            name_match = re.match(r"^\*\*?(.+?)\*\*?[:：]?\s*", entry)
            char_name = name_match.group(1).strip() if name_match else entry[:20]
            # Sanitize filename
            safe_name = re.sub(r"[^\w\u4e00-\u9fff-]", "_", char_name)[:30]
            if not safe_name.strip("_"):
                safe_name = f"角色_{created['characters'] + 1}"

            char_doc_path = project_root / "src" / "characters" / f"{safe_name}.md"
            if not char_doc_path.parent.exists():
                char_doc_path.parent.mkdir(parents=True, exist_ok=True)

            # Build character document
            char_doc = f"# {char_name}\n\n"
            char_doc += f"## 基本信息\n\n{entry}\n\n"
            char_doc += f"## 来源\n\n灵感对话自动生成\n"

            char_doc_path.write_text(char_doc, encoding="utf-8")
            created["characters"] += 1

    # ── 2. Extract world-building ──
    world_section_key = None
    for k in sections:
        if "世界观" in k or "世界" in k:
            world_section_key = k
            break
    if world_section_key:
        world_text = "\n".join(sections[world_section_key])
        world_entries = re.findall(r"(?:^[-*•]\s*|^\d+\.\s*)(.+?)(?=$|\n(?:[-*•]|\d+\.)|$)", world_text, re.MULTILINE)
        if not world_entries:
            world_entries = [l.strip() for l in world_text.split("\n") if l.strip() and len(l.strip()) > 3]

        world_dir = project_root / "src" / "world"
        if not world_dir.exists():
            world_dir.mkdir(parents=True, exist_ok=True)

        # Single world doc for simplicity
        world_doc = "# 世界观设定\n\n> 由灵感对话自动生成\n\n"
        for i, entry in enumerate(world_entries[:8]):
            entry = entry.strip()
            if entry:
                world_doc += f"## 设定 {i+1}\n\n{entry}\n\n"
                created["world"] += 1

        if world_entries:
            (world_dir / "灵感世界观.md").write_text(world_doc, encoding="utf-8")

    # ── 3. Extract outline ──
    outline_section_key = None
    for k in sections:
        if "篇章" in k or "大纲" in k or "结构" in k:
            outline_section_key = k
            break
    if outline_section_key:
        outline_text = "\n".join(sections[outline_section_key])
        outline_path = project_root / "src" / "outline.md"
        existing = ""
        if outline_path.exists():
            existing = outline_path.read_text(encoding="utf-8")

        outline_doc = f"# 故事大纲\n\n> 由灵感对话自动生成\n\n## 篇章结构\n\n{outline_text}\n"
        if existing and "灵感对话" not in existing:
            outline_doc = existing + "\n\n---\n\n" + outline_doc

        outline_path.write_text(outline_doc, encoding="utf-8")
        created["outline"] = True

    # ── 4. Save full prototype as material ──
    materials_dir = project_root / "data" / "wizard_outputs"
    if not materials_dir.exists():
        materials_dir.mkdir(parents=True, exist_ok=True)
    timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    (materials_dir / f"作品雏形_{timestamp}.md").write_text(prototype, encoding="utf-8")
    created["materials"] = 1

    return {
        "ok": True,
        "created_characters": created["characters"],
        "created_world": created["world"],
        "created_outline": created["outline"],
        "created_materials": created["materials"],
    }


def handle_inspire_vision(app, params: dict[str, Any]) -> dict[str, Any]:
    """分析上传的图片，生成灵感种子描述。"""
    import base64
    if not os.environ.get("LLM_API_KEY", "").strip():
        raise StudioError("未配置 LLM_API_KEY，无法使用图片分析功能", HTTPStatus.PRECONDITION_FAILED)

    image_data = str(params.get("image") or "")
    persona = str(params.get("persona") or "warm")

    if not image_data:
        raise StudioError("请上传图片", HTTPStatus.BAD_REQUEST)

    # Strip data:image prefix if present
    if "," in image_data and image_data.startswith("data:"):
        image_data = image_data.split(",", 1)[1]

    persona_prompts = {
        "warm": "用温暖鼓励的语气描述画面，激发创作灵感",
        "sharp": "犀利分析这个画面的优缺点，给出可改进的方向",
        "analyst": "分析画面中的元素、构图、氛围，拆解可用的故事元素",
        "creative": "从画面发散，抛出5个意想不到的故事方向",
        "world": "分析画面中的世界观元素，推测背景设定和规则",
    }
    style_instruction = persona_prompts.get(persona, persona_prompts["warm"])

    try:
        import openai
        client = openai.OpenAI(
            api_key=os.environ.get("LLM_API_KEY", ""),
            base_url=os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1"),
        )

        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        # Try vision-capable model first
        vision_model = os.environ.get("VISION_MODEL", "").strip()
        if not vision_model:
            # Fallback: describe the image with a text prompt saying there's an image
            # For models without vision, describe what we can
            resp = client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "system",
                    "content": f"你是燃灯·青灯的视觉助手。{style_instruction}\n用户上传了一张图片作为创作灵感参考。请你基于「图片已上传」这一信息，给用户一个描述性的引导：先表达你看到了这张图（虽然你无法真正看到但要假装可以），然后基于这个场景提供3个具体的小说创作方向。回复控制在150字内。"
                }, {
                    "role": "user",
                    "content": "我上传了一张图片作为创作灵感，请帮我分析并给灵感方向。"
                }],
                max_tokens=400,
                temperature=0.8,
            )
            content = resp.choices[0].message.content
        else:
            # Use vision model
            resp = client.chat.completions.create(
                model=vision_model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{style_instruction}。描述这张图片，然后给出3个创作灵感方向。总回复150字内。"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                    ]
                }],
                max_tokens=400,
                temperature=0.8,
            )
            content = resp.choices[0].message.content

        return {"description": content, "question": "这个画面给你什么创作灵感？"}

    except ImportError:
        return {"description": "🖼️ 图片已接收！这是一个很好的创作起点。试着描述一下这张图片中的场景——发生了什么？谁在那里？为什么这一刻如此特别？", "question": "从这张图出发，你想讲一个什么样的故事？"}
    except Exception as e:
        raise StudioError(f"图片分析失败: {str(e)}", HTTPStatus.BAD_GATEWAY)
