"""CLI 主入口 — 创建解析器并分发命令。

结构:
    main()         → 创建 parser → 注册所有命令 → 绑定 handler → parse → 分发
    _dispatch()    → 按 command 名路由到对应 handler

handler 绑定采用显式 set_defaults(handler=...) 方式，
确保每个子命令的 handler 可追溯。
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from tools.cli.commands import (
    add_init_command,
    add_setup_command,
    add_goethe_command,
    add_dante_command,
    add_sync_command,
    add_write_command,
    add_multi_write_command,
    add_review_command,
    add_context_command,
    add_assemble_command,
    add_style_command,
    add_setting_command,
    add_source_command,
    add_radar_command,
    add_status_command,
    add_focus_command,
    add_import_command,
    add_export_command,
    add_desk_command,
    add_studio_command,
    add_doctor_command,
    add_agent_command,
)
from tools.cli.handlers import (
    handle_init,
    handle_setup,
    handle_goethe,
    handle_dante,
    handle_sync,
    handle_write,
    handle_multi_write,
    handle_review,
    handle_context,
    handle_assemble,
    handle_style,
    handle_setting,
    handle_source,
    handle_radar,
    handle_status,
    handle_focus,
    handle_import,
    handle_export,
    handle_desk,
    handle_studio,
    handle_doctor,
    handle_agent,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def _create_parser() -> argparse.ArgumentParser:
    """创建顶层解析器并注册所有子命令"""
    from tools.version import __version__

    parser = argparse.ArgumentParser(
        prog="randen",
        description="Randen 长篇小说创作引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Randen {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 注册所有子命令 — 每个函数只做 argparse 定义
    add_init_command(subparsers)
    add_setup_command(subparsers)
    add_goethe_command(subparsers)
    add_dante_command(subparsers)
    add_sync_command(subparsers)
    add_write_command(subparsers)
    add_multi_write_command(subparsers)
    add_review_command(subparsers)
    add_context_command(subparsers)
    add_assemble_command(subparsers)
    add_style_command(subparsers)
    add_setting_command(subparsers)
    add_source_command(subparsers)
    add_radar_command(subparsers)
    add_status_command(subparsers)
    add_focus_command(subparsers)
    add_import_command(subparsers)
    add_export_command(subparsers)
    add_desk_command(subparsers)
    add_studio_command(subparsers)
    add_doctor_command(subparsers)
    add_agent_command(subparsers)

    return parser


def main() -> int:
    """CLI 主入口"""
    parser = _create_parser()
    args = parser.parse_args()

    if not args.command:
        # 当前目录有项目时默认打开工作台
        if (Path.cwd() / "novel_config.yaml").exists():
            return handle_desk(argparse.Namespace(json=False))
        parser.print_help()
        return 0

    handler = getattr(args, "handler", None)
    if handler is None:
        logger = logging.getLogger(__name__)
        logger.error(f"未知命令: {args.command}")
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.info("操作已取消")
        return 130
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"错误: {e}")
        return 1


# ── 兼容别名 ───────────────────────────────────────────────

def _dispatch(args) -> int:
    """命令分发（兼容旧调用方式，新代码请直接用 handler）"""
    return _dispatch_by_command(args.command, args)


def _dispatch_by_command(command: str, args) -> int:
    """按命令名路由到对应 handler（供 goethe/dante 等内部调用）"""
    handler_map = {
        "init": handle_init,
        "setup": handle_setup,
        "sync": handle_sync,
        "write": handle_write,
        "multi-write": handle_multi_write,
        "review": handle_review,
        "context": handle_context,
        "assemble": handle_assemble,
        "style": handle_style,
        "setting": handle_setting,
        "source": handle_source,
        "radar": handle_radar,
        "goethe": handle_goethe,
        "dante": handle_dante,
        "status": handle_status,
        "focus": handle_focus,
        "import": handle_import,
        "export": handle_export,
        "desk": handle_desk,
        "studio": handle_studio,
        "doctor": handle_doctor,
        "agent": handle_agent,
    }
    handler = handler_map.get(command)
    if handler is None:
        logger = logging.getLogger(__name__)
        logger.error(f"未知命令: {command}")
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
