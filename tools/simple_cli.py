#!/usr/bin/env python3
"""燃灯简化命令行 — 一个新手友好的长篇小说 AI 写作入口。

设计原则:
  - 每个动词一个字
  - 每个命令一个目的
  - 错误信息说人话
  - 帮助文档全中文
  - 输出有 rich 面板/表格/进度条

用法:
  randen init           新建一本书（交互式向导）
  randen xie [章号]     写一章（默认写下一章）
  randen kan            查看当前项目状态
  randen shen [章号]    审查章节
  randen gai [章号]     根据审查意见修改
  randen setup          配置模型连接
  randen studio         启动写作工作台 (Web UI)

进阶:
  randen qingdeng       开启青灯规划会话
  randen luobi          开启落笔写作会话
  randen daochu          导出完整书稿 (Markdown/TXT)
  randen daoru <文件>   导入已有书稿
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TimeElapsedColumn,
)
from rich import print as rprint

console = Console()

# ── 依赖检查 ──────────────────────────────────────────────────────────────


def _check_python_version() -> bool:
    """检查 Python 版本是否满足要求。"""
    if sys.version_info < (3, 10):
        console.print(
            "[red]✗ Python 版本过低。燃灯需要 Python >= 3.10，"
            f"当前为 {sys.version_info.major}.{sys.version_info.minor}。"
        )
        return False
    return True


def _check_deps() -> bool:
    """检查必要的 pip 包是否已安装。"""
    missing = []
    for pkg_name, import_name in [
        ("pyyaml", "yaml"),
        ("rich", "rich"),
        ("click", "click"),
        ("pydantic", "pydantic"),
    ]:
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg_name)
    if missing:
        console.print(
            f"[yellow]⚠ 缺少依赖包: {', '.join(missing)}[/yellow]\n"
            f"  请运行: [bold]pip install {' '.join(missing)}[/bold]"
        )
        return False
    return True


def _check_project() -> bool:
    """检查当前目录是否是燃灯项目。"""
    config_path = Path.cwd() / "novel_config.yaml"
    if not config_path.exists():
        console.print(
            "[yellow]⚠ 当前目录不是燃灯项目。[/yellow]\n"
            "  请先运行 [bold]randen init[/bold] 新建一本书，"
            "或进入已有项目的目录。"
        )
        return False
    return True


def _check_llm_config() -> bool:
    """检查 LLM 配置是否就绪。"""
    env_keys = {
        "LLM_PROVIDER": "LLM_PROVIDER",
        "LLM_MODEL": "LLM_MODEL",
        "LLM_API_KEY": "LLM_API_KEY",
    }
    missing = [key for key, env in env_keys.items() if not os.environ.get(env)]
    if missing:
        env_list = ", ".join(f"[bold]{k}[/bold]" for k in missing)
        console.print(
            f"[yellow]⚠ LLM 配置不完整。[/yellow]\n"
            f"  缺少环境变量: {env_list}\n"
            "  请运行 [bold]randen setup[/bold] 配置模型连接。"
        )
        return False
    return True


def _require_project(func):
    """装饰器：要求当前目录是燃灯项目。"""

    @click.pass_context
    def wrapper(ctx, *args, **kwargs):
        if not _check_project():
            ctx.exit(1)
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# ── 健康检查合集 ──────────────────────────────────────────────────────────


def _preflight(full: bool = False) -> bool:
    """执行启动前检查。"""
    ok = True
    if not _check_python_version():
        ok = False
    if not _check_deps():
        ok = False
    if full:
        if not _check_llm_config():
            ok = False
    return ok


def _load_config() -> dict | None:
    """读取 novel_config.yaml。"""
    config_path = Path.cwd() / "novel_config.yaml"
    if not config_path.exists():
        return None
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ── 命令实现 ──────────────────────────────────────────────────────────────


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version="1.0.0", prog_name="randen", message="燃灯 v%(version)s")
def cli(ctx):
    """🏮 燃灯 — 你的长篇小说 AI 写作合伙人

    双 Agent 协作：青灯规划，落笔写作。从灵感到大纲到逐章，守护千万字不崩。
    """
    if ctx.invoked_subcommand is None:
        # 无子命令时显示帮助
        console.print(
            Panel.fit(
                "[bold yellow]🏮 燃灯 — 长篇小说 AI 写作合伙人[/bold yellow]\n\n"
                "双 Agent 协作：青灯规划，落笔写作。\n"
                "从灵感到大纲到逐章写作，守护千万字不崩。\n\n"
                "快速开始:\n"
                "  [bold]randen init[/bold]    新建一本书\n"
                "  [bold]randen setup[/bold]   配置模型连接\n"
                "  [bold]randen xie[/bold]     写下一章\n"
                "  [bold]randen kan[/bold]     查看项目状态\n\n"
                "更多命令: [bold]randen --help[/bold]",
                border_style="yellow",
                title="燃灯 CLI",
            )
        )
        if not _preflight():
            ctx.exit(1)


# ── init ──────────────────────────────────────────────────────────────────


@cli.command("init", help="新建一本书（交互式向导）")
@click.argument("novel_id", required=False, default=None)
@click.option("--title", "-t", default=None, help="书名")
@click.option("--author", "-a", default=None, help="作者名")
def cmd_init(novel_id, title, author):
    """新建一本书，通过交互式问答引导完成项目初始化。

    输入小说 ID（项目标识符，英文字母+数字），
    系统会自动创建目录结构和基础配置文件。
    """
    if not _preflight():
        return

    if not novel_id:
        novel_id = click.prompt("请输入小说 ID（英文标识，如 my_novel）", default="my_novel")

    from tools.novel_service import NovelApplicationService, NovelServiceError

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(description="正在初始化项目...", total=None)
            NovelApplicationService.initialize(Path.cwd(), novel_id)

        config_path = Path.cwd() / "novel_config.yaml"
        if config_path.exists():
            cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            cfg["novel_title"] = title or cfg.get("novel_title", novel_id)
            if author:
                cfg["author"] = author
            config_path.write_text(
                yaml.dump(cfg, allow_unicode=True, default_flow_style=False),
                encoding="utf-8",
            )

        console.print(
            Panel(
                f"[green]✓ 项目已初始化[/green]\n\n"
                f"小说 ID: [bold]{novel_id}[/bold]\n"
                f"目录: {Path.cwd()}\n\n"
                f"接下来:\n"
                f"  1. [bold]randen setup[/bold]  配置模型连接\n"
                f"  2. [bold]randen xie[/bold]    开始写第一章",
                border_style="green",
            )
        )
    except NovelServiceError as e:
        console.print(f"[red]✗ 初始化失败: {e}[/red]")


# ── xie ───────────────────────────────────────────────────────────────────


@cli.command("xie", help="写一章（默认写下一章）")
@click.argument("chapter", required=False, default=None)
@click.option("--no-review", is_flag=True, help="跳过写后审查")
@click.option("--temperature", "-T", type=float, default=0.7, help="写作温度，默认 0.7")
@_require_project
def cmd_xie(chapter, no_review, temperature):
    """写一章正文。

    如果指定章号则写指定章，否则写下一章。

    章号支持格式:
    \b
      ch_001, 001, 第1章, 第一章, 1
    """
    if not _check_llm_config():
        return

    from tools.novel_service import NovelApplicationService, NovelServiceError

    try:
        service = NovelApplicationService(Path.cwd())
        chapter_id = chapter if chapter else "next"
        resolved = service.resolve_chapter_id(chapter_id)
        if not resolved:
            console.print(f"[red]✗ 无法解析章号: {chapter_id}[/red]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                description=f"正在写 [bold]{resolved}[/bold]...", total=None
            )
            result = service.write_chapter(
                {
                    "chapter_id": resolved,
                    "guidance": "",
                    "target_words": 0,
                    "temperature": temperature,
                }
            )
            progress.update(task, completed=True)

        title = result.get("title", "")
        word_count = result.get("word_count", 0)
        console.print(
            Panel(
                f"[green]✓ 章节已生成[/green]\n\n"
                f"章节: [bold]{resolved}[/bold]\n"
                f"标题: {title}\n"
                f"字数: {word_count:,} 字\n"
                f"温度: {temperature}",
                border_style="green",
            )
        )

        if not no_review:
            console.print("\n[dim]正在自动审查...[/dim]")
            review_result = service.review_chapter(resolved)
            score = float(review_result.get("score", 0))
            issues = int(review_result.get("issues", 0))
            passed = review_result.get("passed", False)
            status_icon = "[green]✓[/green]" if passed else "[yellow]⚠[/yellow]"
            console.print(
                f"{status_icon} 审查得分: {score:.0f}/100  |  问题数: {issues}"
            )
            if not passed and issues > 0:
                console.print(
                    "  [dim]运行 [bold]randen shen[/bold] 查看详情，"
                    "或 [bold]randen gai[/bold] 修改。[/dim]"
                )

    except NovelServiceError as e:
        console.print(f"[red]✗ 写作失败: {e}[/red]")


# ── kan ───────────────────────────────────────────────────────────────────


@cli.command("kan", help="查看当前项目状态")
@_require_project
def cmd_kan():
    """查看当前项目的完整状态面板。

    包括进度、章数、字数、人物数量、审查得分等信息。
    """
    from tools.novel_service import NovelApplicationService, NovelServiceError
    from tools.agent.tool_runtime import build_tool_executors

    try:
        service = NovelApplicationService(Path.cwd())
        status = build_tool_executors(Path.cwd())["get_status"]({})

        table = Table(title="📊 项目状态", border_style="cyan")
        table.add_column("指标", style="bold cyan")
        table.add_column("数值", style="white")

        novel_id = status.get("novel_id", "未知")
        current_arc = status.get("current_arc", "-")
        current_chapter = status.get("current_chapter", "-")
        chapters_written = status.get("chapters_written", 0)
        snapshots = status.get("snapshots", 0)

        table.add_row("小说 ID", novel_id)
        table.add_row("当前篇", current_arc)
        table.add_row("当前章", current_chapter)
        table.add_row("已写章节", str(chapters_written))
        table.add_row("快照数", str(snapshots))
        console.print(table)

        try:
            snapshot = service.workspace_state()
            writing_units = getattr(snapshot, "writing_units", 0)
            target = getattr(snapshot, "target_units", 0)
            characters = getattr(snapshot, "characters", 0)
            reviewed = getattr(snapshot, "reviewed_chapters", 0)
            avg_score = getattr(snapshot, "average_review_score", 0)

            detail = Table(border_style="dim")
            detail.add_column("维度", style="dim")
            detail.add_column("值")
            detail.add_row("总字数", f"{writing_units:,} / {target:,}" if target else f"{writing_units:,}")
            detail.add_row("人物", str(characters))
            detail.add_row("已审章节", str(reviewed))
            detail.add_row("平均得分", f"{avg_score:.1f}")
            console.print(detail)
        except Exception:
            pass

    except NovelServiceError as e:
        console.print(f"[red]✗ 读取状态失败: {e}[/red]")


# ── shen ──────────────────────────────────────────────────────────────────


@cli.command("shen", help="审查章节")
@click.argument("chapter", required=False, default=None)
@_require_project
def cmd_shen(chapter):
    """对指定章节执行 37 维度质量审查。

    不指定章号则审查最新一章。
    """
    from tools.novel_service import NovelApplicationService, NovelServiceError

    try:
        service = NovelApplicationService(Path.cwd())
        resolved = service.resolve_chapter_id(chapter, latest=True) if chapter else None
        if resolved is None:
            resolved = service.resolve_chapter_id("latest", latest=True)

        console.print(f"[dim]正在审查 [bold]{resolved}[/bold]...[/dim]")

        result = service.review_chapter(resolved)

        score = float(result.get("score", 0))
        issues = int(result.get("issues", 0))
        passed = result.get("passed", False)

        status_text = "[green]✓ 通过[/green]" if passed else "[yellow]⚠ 需修改[/yellow]"
        console.print(
            Panel(
                f"章节: [bold]{resolved}[/bold]\n"
                f"状态: {status_text}\n"
                f"得分: [bold]{score:.0f}[/bold]/100\n"
                f"问题数: [bold]{issues}[/bold]",
                border_style="green" if passed else "yellow",
                title="📋 审查报告",
            )
        )

        details = result.get("details", result.get("scores", {}))
        if isinstance(details, dict) and details:
            detail_table = Table(border_style="dim")
            detail_table.add_column("维度", style="cyan")
            detail_table.add_column("结果", style="white")
            for key, value in details.items():
                if isinstance(value, (int, float)):
                    detail_table.add_row(key, f"{value:.1f}" if isinstance(value, float) else str(value))
                else:
                    detail_table.add_row(key, str(value)[:60])
            console.print(detail_table)

    except NovelServiceError as e:
        console.print(f"[red]✗ 审查失败: {e}[/red]")


# ── gai ───────────────────────────────────────────────────────────────────


@cli.command("gai", help="根据审查意见修改章节")
@click.argument("chapter", required=False, default=None)
@click.option("--guidance", "-g", default="", help="额外修改指导")
@_require_project
def cmd_gai(chapter, guidance):
    """根据审查意见修改指定章节。

    不指定章号则修改最新一章。
    """
    from tools.novel_service import NovelApplicationService, NovelServiceError

    try:
        service = NovelApplicationService(Path.cwd())
        resolved = service.resolve_chapter_id(chapter, latest=True) if chapter else None
        if resolved is None:
            resolved = service.resolve_chapter_id("latest", latest=True)

        console.print(f"[dim]正在修改 [bold]{resolved}[/bold]...[/dim]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(description="正在重写中...", total=None)
            result = service.write_chapter(
                {
                    "chapter_id": resolved,
                    "guidance": guidance or "根据上一轮审查意见改进本章质量",
                    "target_words": 0,
                    "temperature": 0.7,
                    "is_revision": True,
                }
            )

        title = result.get("title", "")
        word_count = result.get("word_count", 0)
        console.print(
            Panel(
                f"[green]✓ 修改完成[/green]\n\n"
                f"章节: [bold]{resolved}[/bold]\n"
                f"标题: {title}\n"
                f"字数: {word_count:,} 字",
                border_style="green",
            )
        )

    except NovelServiceError as e:
        console.print(f"[red]✗ 修改失败: {e}[/red]")


# ── setup ─────────────────────────────────────────────────────────────────


@cli.command("setup", help="配置模型连接")
def cmd_setup():
    """交互式配置 LLM API 连接。

    支持 OpenAI 兼容接口、Anthropic、自定义端点。
    配置保存在环境变量或 .env 文件中。
    """
    if not _preflight():
        return

    console.print(
        Panel(
            "[bold yellow]🔧 配置大模型连接[/bold yellow]\n\n"
            "燃灯需要连接一个大语言模型来驱动写作和规划。\n"
            "你可以使用任何 OpenAI 兼容接口。",
            border_style="yellow",
        )
    )

    config_path = Path.cwd() / "novel_config.yaml"
    if config_path.exists():
        cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    else:
        cfg = {}

    provider = click.prompt(
        "模型提供商",
        default=os.environ.get("LLM_PROVIDER", "openai"),
        show_default=True,
    )
    model = click.prompt(
        "模型名称",
        default=os.environ.get("LLM_MODEL", "gpt-4o"),
        show_default=True,
    )

    current_key = os.environ.get("LLM_API_KEY", "")
    masked = f"{current_key[:4]}...{current_key[-4:]}" if len(current_key) > 8 else "(未设置)"
    api_key = click.prompt(
        "API Key",
        default=current_key,
        show_default=False,
        hide_input=True,
    )

    base_url = click.prompt(
        "API 地址（留空使用默认）",
        default=os.environ.get("LLM_BASE_URL", ""),
        show_default=True,
    )

    cfg["llm"] = {"provider": provider, "model": model}
    config_path.write_text(
        yaml.dump(cfg, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )

    env_path = Path.cwd() / ".env"
    existing_env = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    updates = {
        "LLM_PROVIDER": provider,
        "LLM_MODEL": model,
        "LLM_API_KEY": api_key,
    }
    if base_url:
        updates["LLM_BASE_URL"] = base_url

    new_lines = []
    seen_keys = set()
    for line in existing_env.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            seen_keys.add(key)
            new_lines.append(f"{key}={updates[key]}")
        else:
            new_lines.append(line)
    for k, v in updates.items():
        if k not in seen_keys:
            new_lines.append(f"{k}={v}")
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    console.print(
        Panel(
            f"[green]✓ 配置已保存[/green]\n\n"
            f"提供商: [bold]{provider}[/bold]\n"
            f"模型: [bold]{model}[/bold]\n"
            f"配置文件: {config_path}\n"
            f"环境变量: {env_path}",
            border_style="green",
        )
    )


# ── studio ────────────────────────────────────────────────────────────────


@cli.command("studio", help="启动写作工作台 (Web UI)")
@click.option("--port", "-p", type=int, default=5000, help="端口号，默认 5000")
@click.option("--no-open", is_flag=True, help="不自动打开浏览器")
@_require_project
def cmd_studio(port, no_open):
    """启动燃灯写作工作台 Web UI。

    在浏览器中打开图形化写作界面。
    """
    try:
        import flask  # noqa: F401
    except ImportError:
        console.print(
            "[red]✗ 缺少 flask 包。请安装:[/red]\n"
            "  [bold]pip install flask[/bold]"
        )
        return

    from tools.studio import StudioError, run_studio

    try:
        console.print(f"[dim]正在启动写作工作台 (端口 {port})...[/dim]")
        run_studio(Path.cwd(), port=port, open_browser=not no_open)
    except (OSError, StudioError) as e:
        console.print(f"[red]✗ 启动失败: {e}[/red]")


# ── qingdeng ──────────────────────────────────────────────────────────────


@cli.command("qingdeng", help="开启青灯规划会话")
@_require_project
def cmd_qingdeng():
    """启动青灯（Goethe）长会话规划界面。

    青灯负责：灵感整理、人物设定、世界观构建、大纲规划。
    在资产成熟后可显式交接给落笔写作。
    """
    from tools.goethe import run_goethe

    console.print("[dim]🔥 燃起青灯，开始规划...[/dim]")
    run_goethe()


# ── luobi ─────────────────────────────────────────────────────────────────


@cli.command("luobi", help="开启落笔写作会话")
@_require_project
def cmd_luobi():
    """启动落笔（Dante）长会话正文创作界面。

    落笔负责：章节写作、37 维度审查、状态结算。
    """
    from tools.agent.dante import run_dante

    console.print("[dim]🖊️ 提起落笔，开始写作...[/dim]")
    run_dante()


# ── daochu ────────────────────────────────────────────────────────────────


@cli.command("daochu", help="导出完整书稿")
@click.option("--format", "-f", "fmt", type=click.Choice(["md", "txt"]), default="md",
              help="导出格式，默认 md")
@click.option("--output", "-o", default=None, help="输出文件路径")
@click.option("--title", default=None, help="书稿标题")
@_require_project
def cmd_daochu(fmt, output, title):
    """导出完整小说书稿为 Markdown 或纯文本。

    所有章节按顺序合并，附带标题和元信息。
    """
    from tools.novel_service import NovelApplicationService, NovelServiceError
    from tools.novel_workspace import NovelWorkspace

    project_root = Path.cwd()
    try:
        service = NovelApplicationService(project_root)
        config = _load_config() or {}
        novel_id = config.get("novel_id", "novel")
        book_title = title or config.get("novel_title", novel_id)

        fmt_map = {"md": "markdown", "txt": "txt"}
        export_format = fmt_map.get(fmt, "txt")

        if not output:
            (project_root / "exports").mkdir(parents=True, exist_ok=True)
            output = str(project_root / "exports" / f"{novel_id}.{fmt}")

        console.print(f"[dim]正在导出书稿 ({fmt.upper()})...[/dim]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(description="正在合并章节...", total=None)
            result_path = service.export_book(
                Path(output),
                format_name=export_format,
                title=book_title,
            )

        file_size = result_path.stat().st_size if result_path.exists() else 0
        console.print(
            Panel(
                f"[green]✓ 书稿已导出[/green]\n\n"
                f"文件: [bold]{result_path}[/bold]\n"
                f"大小: {file_size:,} 字节\n"
                f"格式: {fmt.upper()}",
                border_style="green",
            )
        )

    except NovelServiceError as e:
        console.print(f"[red]✗ 导出失败: {e}[/red]")


# ── daoru ─────────────────────────────────────────────────────────────────


@cli.command("daoru", help="导入已有书稿")
@click.argument("source", type=click.Path(exists=True))
@click.option("--arc", "-a", default=None, help="目标篇 ID")
@click.option("--start", "-s", type=int, default=1, help="起始章号，默认 1")
@click.option("--force", is_flag=True, help="强制覆盖已有章节")
@_require_project
def cmd_daoru(source, arc, start, force):
    """导入已有的 TXT 或 Markdown 书稿。

    按章节分割规则自动识别章节，导入为燃灯可管理的章节文件。
    """
    from tools.novel_service import NovelApplicationService, NovelServiceError

    try:
        source_path = Path(source)
        console.print(f"[dim]正在导入: {source_path.name}[/dim]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(description="正在解析并导入...", total=None)
            result = NovelApplicationService(Path.cwd()).import_book(
                source_path.expanduser(),
                arc_id=arc,
                start_number=start,
                force=bool(force),
            )

        imported = len(result.get("imported", []))
        words = result.get("writing_units", 0)
        next_ch = result.get("next_chapter", "?")
        console.print(
            Panel(
                f"[green]✓ 导入完成[/green]\n\n"
                f"已导入: [bold]{imported}[/bold] 章\n"
                f"合计: {words:,} 字\n"
                f"下一章: {next_ch}",
                border_style="green",
            )
        )

    except NovelServiceError as e:
        console.print(f"[red]✗ 导入失败: {e}[/red]")


# ── 主入口 ────────────────────────────────────────────────────────────────


def main():
    """简化 CLI 主入口。"""
    if not _check_python_version():
        sys.exit(1)
    if not _check_deps():
        sys.exit(1)
    cli()


if __name__ == "__main__":
    main()
