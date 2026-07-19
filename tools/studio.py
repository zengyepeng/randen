"""兼容层——保持 `from tools.studio import ...` 导入不变。

实际实现已迁移至 tools/studio/ 包。
"""

from __future__ import annotations

from tools.studio.app import MAX_DOCUMENT_BYTES, StudioApplication, StudioError
from tools.studio.server import RandenStudioServer, create_server
from tools.studio import run_studio

__all__ = [
    "StudioApplication",
    "StudioError",
    "RandenStudioServer",
    "create_server",
    "run_studio",
    "MAX_DOCUMENT_BYTES",
]
