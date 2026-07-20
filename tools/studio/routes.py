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
    handle_idea,
    handle_opening,
    handle_faq,
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
    "/api/project/init":    (handle_project_init,    False),
    "/api/focus":           (handle_focus,           False),
    "/api/model":           (handle_model,           False),
    "/api/market":          (handle_market,          False),
    "/api/dissect":         (handle_dissect,         False),
    "/api/idea":            (handle_idea,            False),
    "/api/opening":         (handle_opening,         False),
    "/api/faq":             (handle_faq,             False),
    "/api/write":           (handle_write,           True),
    "/api/review":          (handle_review,          True),
    "/api/sync":            (handle_sync,            True),
    "/api/document/create": (handle_document_create, True),
    "/api/import":          (handle_import,          True),
    "/api/foreshadowing":   (handle_foreshadowing,   True),
    "/api/chat":            (handle_chat,            True),
    "/api/source":          (handle_source,          True),
}
