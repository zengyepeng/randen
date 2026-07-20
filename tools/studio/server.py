"""Randen Studio HTTP 服务器——请求处理、路由分发、静态资源服务。"""

from __future__ import annotations
import os

import json
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

from .app import MAX_DOCUMENT_BYTES, StudioApplication, StudioError
from .handlers import handle_document_write, handle_export
from .routes import GET_ROUTES, POST_ROUTES
from .templates import serve_brand_logo_content, serve_static_content
_LOGIN_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>燃灯 · 登录</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{display:flex;align-items:center;justify-content:center;min-height:100vh;background:#1a1a18;color:#f4f4ef;font-family:system-ui,sans-serif}
.card{background:#20201e;border-radius:12px;padding:40px 32px;width:340px;max-width:90vw;text-align:center;border:1px solid #3a3a36}
h1{font-size:24px;margin-bottom:8px;color:#dbb85a}
p{color:#94948c;font-size:14px;margin-bottom:24px}
input{width:100%;padding:12px 16px;border-radius:8px;border:1px solid #56564f;background:#171715;color:#f4f4ef;font-size:16px;outline:none;text-align:center}
input:focus{border-color:#dbb85a}
button{width:100%;padding:12px;margin-top:12px;border-radius:8px;border:none;background:#dbb85a;color:#171715;font-size:16px;font-weight:650;cursor:pointer}
button:active{opacity:.8}
.error{color:#ff8b7e;font-size:13px;margin-top:12px;display:none}
</style></head>
<body>
<form id="f" class="card" onsubmit="return login()">
<h1>🔥 燃灯</h1>
<p>输入访问密码进入写作工作室</p>
<input id="p" type="password" placeholder="密码" autofocus>
<button type="submit">进入</button>
<p id="e" class="error">密码错误</p>
</form>
<script>
function login(){var p=document.getElementById('p').value;if(!p){document.getElementById('e').style.display='block';return false}
document.cookie='randen_auth='+p+';path=/;max-age=86400';location.reload();return false}
</script>
</body></html>"""


WRITE_HEADER = "X-Randen-Studio"
STATIC_ROOT = Path(__file__).parent.parent / "studio_assets"


class StudioRequestHandler(SimpleHTTPRequestHandler):
    """Randen Studio HTTP 请求处理器。"""

    server_version = "RandenStudio/5.8"
    def _check_auth(self) -> bool:
        """验证工作室访问密码"""
        studio_password = os.environ.get("RANDEN_STUDIO_PASSWORD", "")
        if not studio_password:
            return True  # 未设密码则允许访问
        auth = self.headers.get("Authorization", "")
        if auth == f"Bearer {studio_password}":
            return True
        cookie = self.headers.get("Cookie", "")
        if f"randen_auth={studio_password}" in cookie:
            return True
        return False

    def _auth_fail(self) -> None:
        """返回登录页面"""
        self.send_response(HTTPStatus.OK)
        self._security_headers()
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(_LOGIN_PAGE)))
        self.end_headers()
        self.wfile.write(_LOGIN_PAGE.encode("utf-8"))


    @property
    def app(self) -> StudioApplication:
        return getattr(self.server, "app")  # type: ignore[no-any-return]


    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        
        # 密码验证
        if not self._check_auth():
            # 允许静态资源无密码加载
            if not parsed.path.startswith("/api/") and parsed.path != "/":
                pass  # 静态资源放过
            elif parsed.path == "/" or parsed.path.startswith("/api/"):
                self._auth_fail()
                return

        try:
            if parsed.path == "/api/export":
                self.app.require_project()
                format_name = parse_qs(parsed.query).get("format", ["md"])[0]
                result = handle_export(self.app, {"format": format_name})
                self._send_export(result)
                return
            if parsed.path in {"/brand/logo.svg", "/brand/logo-dark.svg"}:
                dark = parsed.path.endswith("dark.svg")
                content, content_type = serve_brand_logo_content(STATIC_ROOT, dark)
                self._send_binary(content, content_type)
                return
            handler, needs_project = GET_ROUTES.get(parsed.path, (None, False))
            if handler is not None:
                if needs_project:
                    self.app.require_project()
                self._json(handler(self.app, query))
                return
            self._serve_static(parsed.path)
        except StudioError as exc:
            self._json({"error": str(exc)}, status=exc.status)
        except Exception:
            self._json({"error": "Studio 内部错误"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_PUT(self) -> None:
        try:
            self._require_write_header()
            if urlparse(self.path).path != "/api/document":
                raise StudioError("接口不存在", HTTPStatus.NOT_FOUND)
            self.app.require_project()
            self._json(handle_document_write(self.app, self._body_json()))
        except StudioError as exc:
            self._json({"error": str(exc)}, status=exc.status)

    def do_POST(self) -> None:
        try:
            self._require_write_header()
            route = urlparse(self.path).path
            handler, needs_project = POST_ROUTES.get(route, (None, False))
            if handler is None:
                raise StudioError("接口不存在", HTTPStatus.NOT_FOUND)
            if needs_project:
                self.app.require_project()
            self._json(handler(self.app, self._body_json()))
        except StudioError as exc:
            self._json({"error": str(exc)}, status=exc.status)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
        self._security_headers()
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        if self.path.startswith("/api/") and not self.path.startswith("/api/health"):
            super().log_message(format, *args)

    def _serve_static(self, request_path: str) -> None:
        content, content_type = serve_static_content(STATIC_ROOT, request_path)
        self._send_binary(content, content_type)

    def _send_binary(self, content: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self._security_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_export(self, result: dict[str, Any]) -> None:
        filename = str(result["filename"])
        content = result["content"]
        mime = str(result["mime"])
        self.send_response(HTTPStatus.OK)
        self._security_headers()
        self.send_header("Content-Type", mime)
        self.send_header("Content-Disposition",
                         f"attachment; filename*=UTF-8''{quote(filename)}")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _body_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise StudioError("无效请求长度") from exc
        if length <= 0 or length > MAX_DOCUMENT_BYTES + 65536:
            raise StudioError("无效请求体", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StudioError("请求 JSON 无效") from exc
        if not isinstance(payload, dict):
            raise StudioError("请求必须是 JSON 对象")
        return payload

    def _require_write_header(self) -> None:
        if self.headers.get(WRITE_HEADER) != "1":
            raise StudioError("缺少 Studio 写入凭证", HTTPStatus.FORBIDDEN)

    def _json(self, payload: Any, status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self._security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; connect-src 'self'; frame-ancestors 'none'",
        )
        self.send_header("Cache-Control", "no-store")


class RandenStudioServer(ThreadingHTTPServer):
    """Randen Studio 多线程 HTTP 服务器。"""
    app: StudioApplication


def create_server(
    project_root: Path,
    *,
    host: str = "0.0.0.0",
    port: int = 4567,
    writer_executor: Any = None,
    review_executor: Any = None,
    chat_executor: Any = None,
    source_executor: Any = None,
) -> RandenStudioServer:
    """创建 Randen Studio HTTP 服务器实例。"""
    if not STATIC_ROOT.is_dir():
        raise StudioError(f"Studio 静态资源缺失: {STATIC_ROOT}")
    app = StudioApplication(
        project_root,
        writer_executor=writer_executor,
        review_executor=review_executor,
        chat_executor=chat_executor,
        source_executor=source_executor,
    )
    handler = partial(StudioRequestHandler, directory=str(STATIC_ROOT))
    server = RandenStudioServer((host, port), handler)
    server.app = app
    return server
