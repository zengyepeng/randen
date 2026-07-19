"""CLI 命令注册 — 纯 argparse 定义，不包含业务逻辑。

每个 _add_*_command 函数只做两件事：
1. 创建子命令解析器（add_parser / add_subparsers）
2. 绑定对应的 handler（set_defaults(handler=...)）
"""

from __future__ import annotations

import argparse
from collections.abc import Callable


def add_init_command(subparsers: argparse._SubParsersAction) -> None:
    """init — 初始化新项目"""
    from tools.cli.handlers import handle_init
    p = subparsers.add_parser("init", help="初始化新项目（无参数时启动交互式向导）")
    p.add_argument("novel_id", nargs="?", default=None, help="小说 ID（不指定则启动交互式向导）")
    p.add_argument("--template", "-t", default="default", help="模板类型")
    p.set_defaults(handler=handle_init)


def add_setup_command(subparsers: argparse._SubParsersAction) -> None:
    """setup — AI 模型配置向导"""
    from tools.cli.handlers import handle_setup
    p = subparsers.add_parser(
        "setup",
        help="配置 AI 模型（交互式向导）",
        description="配置 AI 模型：选择提供商、输入 API Key、测试连接。",
    )
    p.set_defaults(handler=handle_setup)


def add_goethe_command(subparsers: argparse._SubParsersAction) -> None:
    """goethe — 长期会话规划入口"""
    from tools.cli.handlers import handle_goethe
    p = subparsers.add_parser(
        "goethe",
        help="长期会话规划入口：启动 Goethe 持续规划 shell",
        description="长期会话规划入口：启动 Goethe 持续规划 shell。",
    )
    p.add_argument("--novel-id", help="小说 ID（默认从 novel_config.yaml 读取）")
    p.set_defaults(handler=handle_goethe)


def add_dante_command(subparsers: argparse._SubParsersAction) -> None:
    """dante — 长期会话主入口"""
    from tools.cli.handlers import handle_dante
    p = subparsers.add_parser(
        "dante",
        help="长期会话主入口：启动 Dante 持续对话 shell",
        description="长期会话主入口：启动 Dante 持续对话 shell。",
    )
    p.set_defaults(handler=handle_dante)


def add_sync_command(subparsers: argparse._SubParsersAction) -> None:
    """sync — 同步 src 到 data"""
    from tools.cli.handlers import handle_sync
    p = subparsers.add_parser("sync", help="同步 src 到 data（大纲/角色）")
    p.add_argument("--novel-id", help="小说 ID（默认从 novel_config.yaml 读取）")
    p.add_argument("--check", action="store_true", help="仅检查是否存在未同步变更")
    p.add_argument("--json", action="store_true", help="输出 JSON 结果（便于脚本/Agent 解析）")
    p.set_defaults(handler=handle_sync)


def add_write_command(subparsers: argparse._SubParsersAction) -> None:
    """write — 写章节"""
    from tools.cli.handlers import handle_write
    p = subparsers.add_parser("write", help="写章节")
    p.add_argument("chapter", nargs="?", default="next", help="章节 ID 或 'next'")
    p.add_argument("--no-review", action="store_true", help="跳过审查")
    p.add_argument("--temperature", "-T", type=float, default=0.7, help="写作温度")
    p.set_defaults(handler=handle_write)


def add_multi_write_command(subparsers: argparse._SubParsersAction) -> None:
    """multi-write — 多 Agent 编排写章节"""
    from tools.cli.handlers import handle_multi_write
    p = subparsers.add_parser("multi-write", help="使用多 Agent 编排写章节")
    p.add_argument("chapter", nargs="?", default="next", help="章节 ID 或 'next'")
    p.add_argument("--temperature", "-T", type=float, default=0.7, help="写作温度")
    p.add_argument("--no-review", action="store_true", help="跳过审查")
    p.add_argument("--show-packet", action="store_true", help="先输出组装包")
    p.add_argument("--packet-output-dir", help="组装包测试输出目录（自动命名）")
    p.set_defaults(handler=handle_multi_write)


def add_review_command(subparsers: argparse._SubParsersAction) -> None:
    """review — 审查章节"""
    from tools.cli.handlers import handle_review
    p = subparsers.add_parser("review", help="审查章节")
    p.add_argument("chapter", nargs="?", default="latest", help="章节 ID 或 'latest'")
    p.add_argument("--strict", action="store_true", help="严格模式")
    p.set_defaults(handler=handle_review)


def add_context_command(subparsers: argparse._SubParsersAction) -> None:
    """context — 构建上下文"""
    from tools.cli.handlers import handle_context
    p = subparsers.add_parser("context", help="构建上下文")
    p.add_argument("chapter", nargs="?", default="next", help="章节 ID")
    p.add_argument("--show", action="store_true", help="显示上下文内容")
    p.set_defaults(handler=handle_context)


def add_assemble_command(subparsers: argparse._SubParsersAction) -> None:
    """assemble — 按 V2 规则组装章节上下文包"""
    from tools.cli.handlers import handle_assemble
    p = subparsers.add_parser("assemble", help="按 V2 规则组装章节上下文包")
    p.add_argument("chapter", nargs="?", default="next", help="章节 ID 或 'next'")
    p.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="输出格式（默认 markdown）",
    )
    p.add_argument("--output", "-o", help="输出文件路径")
    p.add_argument("--output-dir", help="测试输出目录（自动命名文件）")
    p.add_argument("--no-print", action="store_true", help="不在终端打印结果")
    p.set_defaults(handler=handle_assemble)


def add_style_command(subparsers: argparse._SubParsersAction) -> None:
    """style — 风格管理"""
    from tools.cli.handlers import handle_style
    p = subparsers.add_parser("style", help="风格管理")
    p.set_defaults(handler=handle_style)
    sub = p.add_subparsers(dest="style_action")

    extract = sub.add_parser("extract", help="从用户提供文本提取风格与设定")
    extract.add_argument(
        "source_id",
        help="来源 ID（写入 data/novels/{id}/data/sources/{source_id}/）",
    )
    extract.add_argument("--source", required=True, help="源文本路径")
    extract.add_argument("--chunk-size", type=int, default=30000, help="分块字数（默认30000）")

    synthesize = sub.add_parser("synthesize", help="合成风格")
    synthesize.add_argument("--novel-id", default="current", help="小说 ID")


def add_setting_command(subparsers: argparse._SubParsersAction) -> None:
    """setting — 设定来源管理"""
    from tools.cli.handlers import handle_setting
    p = subparsers.add_parser("setting", help="设定来源管理")
    p.set_defaults(handler=handle_setting)
    sub = p.add_subparsers(dest="setting_action")

    extract = sub.add_parser("extract", help="从用户提供文本提取设定与世界信息")
    extract.add_argument(
        "source_id",
        help="来源 ID（写入 data/novels/{id}/data/sources/{source_id}/）",
    )
    extract.add_argument("--source", required=True, help="源文本路径")
    extract.add_argument("--chunk-size", type=int, default=30000, help="分块字数（默认30000）")


def add_source_command(subparsers: argparse._SubParsersAction) -> None:
    """source — 来源文本 source pack 管理"""
    from tools.cli.handlers import handle_source
    p = subparsers.add_parser("source", help="来源文本 source pack 管理")
    p.set_defaults(handler=handle_source)
    sub = p.add_subparsers(dest="source_action")

    review = sub.add_parser("review", help="审阅提取后的 source pack")
    review.add_argument("source_id", help="来源 ID")
    review.add_argument(
        "--novel-id",
        default="current",
        help="小说 ID（默认从 novel_config.yaml 读取）",
    )

    promote = sub.add_parser("promote", help="将 source pack 晋升到当前项目")
    promote.add_argument("source_id", help="来源 ID")
    promote.add_argument(
        "--novel-id",
        default="current",
        help="小说 ID（默认从 novel_config.yaml 读取）",
    )
    promote.add_argument(
        "--target",
        choices=["style", "setting", "world", "all"],
        default="all",
        help="晋升目标",
    )


def add_radar_command(subparsers: argparse._SubParsersAction) -> None:
    """radar — 市场趋势分析"""
    from tools.cli.handlers import handle_radar
    p = subparsers.add_parser("radar", help="市场趋势分析")
    p.add_argument("--platform", "-p", nargs="+", help="平台列表（默认全部）")
    p.add_argument("--top", "-n", type=int, default=5, help="每个平台推荐数")
    p.add_argument("--output", "-o", help="保存结果到文件")
    p.set_defaults(handler=handle_radar)


def add_status_command(subparsers: argparse._SubParsersAction) -> None:
    """status — 查看项目状态"""
    from tools.cli.handlers import handle_status
    p = subparsers.add_parser("status", help="查看项目状态")
    p.add_argument("--json", action="store_true", help="输出结构化 JSON")
    p.set_defaults(handler=handle_status)


def add_focus_command(subparsers: argparse._SubParsersAction) -> None:
    """focus — 管理近期创作罗盘"""
    from tools.cli.handlers import handle_focus
    p = subparsers.add_parser("focus", help="查看或设置近期创作罗盘")
    p.set_defaults(handler=handle_focus)
    sub = p.add_subparsers(dest="focus_action")
    sub.add_parser("show", help="显示当前创作罗盘")
    set_cmd = sub.add_parser("set", help="设置当前阶段目标与硬约束")
    set_cmd.add_argument("goal", help="当前阶段最重要的叙事目标")
    set_cmd.add_argument("--keep", action="append", default=[], help="必须保留，可重复")
    set_cmd.add_argument("--avoid", action="append", default=[], help="必须避免，可重复")
    set_cmd.add_argument("--note", action="append", default=[], help="写作备注，可重复")
    sub.add_parser("clear", help="清空近期创作罗盘")


def add_import_command(subparsers: argparse._SubParsersAction) -> None:
    """import — 导入已有小说正文"""
    from tools.cli.handlers import handle_import
    p = subparsers.add_parser("import", help="从 TXT/Markdown 导入已有小说章节")
    p.add_argument("source", help="源文件路径")
    p.add_argument("--arc", help="导入到指定篇，默认使用 current_arc")
    p.add_argument("--start", type=int, help="指定起始章节号；默认追加到现有正文后")
    p.add_argument("--force", action="store_true", help="允许覆盖同名目标章节")
    p.set_defaults(handler=handle_import)


def add_export_command(subparsers: argparse._SubParsersAction) -> None:
    """export — 导出整书"""
    from tools.cli.handlers import handle_export
    p = subparsers.add_parser("export", help="按章节顺序导出整书")
    p.add_argument("--format", choices=["md", "txt"], default="md", help="导出格式")
    p.add_argument("--output", "-o", help="输出路径")
    p.add_argument("--title", help="覆盖导出书名")
    p.set_defaults(handler=handle_export)


def add_desk_command(subparsers: argparse._SubParsersAction) -> None:
    """desk — 小说工作台"""
    from tools.cli.handlers import handle_desk
    p = subparsers.add_parser("desk", help="打开小说专用终端工作台")
    p.add_argument("--json", action="store_true", help="输出结构化 JSON")
    p.set_defaults(handler=handle_desk)


def add_studio_command(subparsers: argparse._SubParsersAction) -> None:
    """studio — 本地 Web 小说工作台"""
    from tools.cli.handlers import handle_studio
    p = subparsers.add_parser("studio", help="启动本地 Web 小说工作台")
    p.add_argument("--port", "-p", type=int, default=4567, help="监听端口（默认 4567）")
    p.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    p.set_defaults(handler=handle_studio)


def add_doctor_command(subparsers: argparse._SubParsersAction) -> None:
    """doctor — 环境与路径自检"""
    from tools.cli.handlers import handle_doctor
    p = subparsers.add_parser("doctor", help="环境与路径自检")
    p.set_defaults(handler=handle_doctor)


def add_agent_command(subparsers: argparse._SubParsersAction) -> None:
    """agent — 已退役"""
    from tools.cli.handlers import handle_agent
    p = subparsers.add_parser(
        "agent",
        help="已退役：请改用 randen dante",
        description="已退役：请改用 randen dante",
    )
    p.set_defaults(handler=handle_agent)


# ── 按命令名映射 handler 引用的注册表 ──────────────────────
# 供 main.py 批量调用。

COMMANDS: list[Callable[[argparse._SubParsersAction], None]] = [
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
]
