"""Randen Studio 静态资源与模板渲染模块。"""

from __future__ import annotations

import mimetypes
from http import HTTPStatus
from pathlib import Path

from .app import StudioError


def serve_static_content(static_root: Path, request_path: str) -> tuple[bytes, str]:
    """解析请求路径并返回静态文件内容与 MIME 类型。"""
    relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
    resolved = (static_root / relative).resolve()
    # 安全检查：确保解析后的路径在 static_root 内
    if (static_root.resolve() not in resolved.parents
            and resolved != static_root.resolve()):
        raise StudioError("资源不存在", HTTPStatus.NOT_FOUND)
    path = resolved if resolved.is_file() else static_root / "index.html"
    content = path.read_bytes()
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return content, content_type


def serve_brand_logo_content(static_root: Path, dark: bool) -> tuple[bytes, str]:
    """返回品牌 Logo 文件内容与 MIME 类型。"""
    filename = "logo-dark.svg" if dark else "logo.svg"
    path = static_root / filename
    if not path.is_file():
        raise StudioError("品牌资源不存在", HTTPStatus.NOT_FOUND)
    return path.read_bytes(), "image/svg+xml"
