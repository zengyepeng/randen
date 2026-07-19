"""Randen Studio——本地小说创作工作台。

使用方式：
    from tools.studio import StudioApplication, RandenStudioServer, run_studio, StudioError

    # 以编程方式创建应用
    app = StudioApplication(project_root)

    # 启动 HTTP 服务器
    run_studio(project_root, port=4567)
"""

from __future__ import annotations

import webbrowser
from pathlib import Path

from .app import MAX_DOCUMENT_BYTES, StudioApplication, StudioError
from .server import RandenStudioServer, create_server

__all__ = [
    "StudioApplication",
    "StudioError",
    "RandenStudioServer",
    "create_server",
    "run_studio",
    "MAX_DOCUMENT_BYTES",
]


def run_studio(
    project_root: Path,
    *,
    port: int = 4567,
    open_browser: bool = True,
) -> int:
    """启动 Randen Studio HTTP 服务器（阻塞）。"""
    server = create_server(project_root, port=port)
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"Randen Studio: {url}")
    print("按 Ctrl+C 停止")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStudio 已停止")
    finally:
        server.server_close()
    return 0
