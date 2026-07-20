"""Randen Studio 路由表——仅定义 API 端点映射，业务逻辑在 handlers.py。"""

from __future__ import annotations

from typing import Any

from .handlers import (
    handle_chat,
    handle_context,
    handle_continuity,
    handle_document_create,
    handle_document_read,
    handle_document_write,
    handle_export,
    handle_focus,
    handle_foreshadowing,
    handle_health,
    handle_import,
    handle_model,
    handle_project_init,
    handle_review,
    handle_source,
    handle_sync,
    handle_workspace,
    handle_write,
    handle_market,
    handle_dissect,
    handle_dissect_deep,
    handle_dissect_multi,
    handle_merge_dissections,
    handle_idea,
    handle_opening,
    handle_faq,
    handle_save_result,
    handle_character_guide,
    handle_generate_outline,
    handle_epub_extract,
    handle_ai_dissect,
    handle_ai_imitate,
)

# (处理器, 是否需要项目已初始化)
GET_ROUTES: dict[str, tuple[Any, bool]] = {
    "/api/health":     (handle_health,     False),
    "/api/workspace":  (handle_workspace,  False),
    "/api/continuity": (handle_continuity, True),
    "/api/context":    (handle_context,    True),
    "/api/document":   (handle_document_read, True),
}

POST_ROUTES: dict[str, tuple[Any, bool]] = {
    "/api/project/init":      (handle_project_init,    False),
    "/api/focus":             (handle_focus,           False),
    "/api/model":             (handle_model,           False),
    "/api/market":            (handle_market,          False),
    "/api/dissect":           (handle_dissect,         False),
    "/api/dissect/deep":      (handle_dissect_deep,    False),
    "/api/dissect/multi":     (handle_dissect_multi,   False),
    "/api/dissect/merge":     (handle_merge_dissections, False),
    "/api/idea":              (handle_idea,            False),
    "/api/opening":           (handle_opening,         False),
    "/api/faq":               (handle_faq,             False),
    "/api/save":              (handle_save_result,     False),
    "/api/character_guide":   (handle_character_guide, False),
    "/api/generate_outline":  (handle_generate_outline, False),
    "/api/epub":              (handle_epub_extract,    False),
    "/api/ai_dissect":        (handle_ai_dissect,      False),
    "/api/ai_imitate":        (handle_ai_imitate,      False),
    "/api/write":             (handle_write,           True),
    "/api/review":            (handle_review,          True),
    "/api/sync":              (handle_sync,            True),
    "/api/document/create":   (handle_document_create, True),
    "/api/import":            (handle_import,          True),
    "/api/foreshadowing":     (handle_foreshadowing,   True),
    "/api/chat":              (handle_chat,            True),
    "/api/source":            (handle_source,          True),
}
