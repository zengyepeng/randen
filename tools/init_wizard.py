#!/usr/bin/env python3
"""燃灯新手向导 — init 命令

交互式向导：30 秒从零到写第一章。
引导用户创建小说项目，感知项目结构，然后进入写作。
"""

from __future__ import annotations

import sys
import re
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box
    from rich.text import Text
    from rich.columns import Columns
    from rich.layout import Layout
except ImportError:
    Console = None

try:
    import yaml
except ImportError:
    yaml = None

# 支持的题材
GENRES = [
    "修仙", "东方玄幻", "都市", "科幻", "历史",
    "悬疑", "奇幻", "武侠", "游戏", "轻小说", "其他",
]

# 建议下一步
NEXT_STEPS = """[bold cyan]下一步你可以：[/]

  [white]1. 打开大纲，规划故事骨架[/]
     $ randen goethe       # 和策划编辑聊天定大纲
     $ vim src/outline.md     # 或者直接写大纲

  [white]2. 创建核心角色[/]
     $ randen goethe       # 让 AI 帮你生成人设

  [white]3. 写第一章！[/]  ← [bold yellow]从这里开始[/]
     [green]$ randen write next[/]

  [white]4. 查看项目状态[/]
     $ randen desk         # 小说工作台
     $ randen status       # 进度概览"""


def _make_console():
    if Console:
        return Console()
    return None


class InitWizard:
    """交互式新手向导"""

    def __init__(self):
        self.console = _make_console()
        self.print = self.console.print if self.console else print
        self.project_root = Path.cwd()
        self.novel_id: str = ""
        self.title: str = ""
        self.genre: str = ""
        self.summary: str = ""

    def logo(self) -> str:
        """燃灯 ASCII Logo"""
        return (
            "   ╔═══════════════════════════════════╗\n"
            "   ║       ██████  ██      ██          ║\n"
            "   ║      ██       ██      ██          ║\n"
            "   ║      ██       ██      ██          ║\n"
            "   ║      ██       ██      ██          ║\n"
            "   ║       ██████  ██████  ██████      ║\n"
            "   ║           燃  灯  创  作  引  擎   ║\n"
            "   ╚═══════════════════════════════════╝"
        )

    def run(self) -> int:
        """启动向导主流程"""
        # ── 欢迎画面 ────────────────────────────
        self._welcome()
        if not self._check_project():
            return 1

        # ── 步骤 1: 书名 ──────────────────
        self.title = self._ask_title()
        if self.title is None:
            return 1

        # ── 步骤 2: 题材 ──────────────────
        self.genre = self._ask_genre()
        if self.genre is None:
            return 1

        # ── 步骤 3: 简介 ──────────────────
        self.summary = self._ask_summary()
        if self.summary is None:
            return 1

        # ── 步骤 4: 模型检查 ──────────────
        self._check_model()

        # ── 步骤 5: 创建项目 ──────────────
        if not self._create_project():
            return 1

        # ── 完成 ─────────────────────────
        self._show_completion()
        return 0

    def _welcome(self):
        """显示欢迎画面"""
        if self.console:
            logo_text = Text(self.logo(), style="bold cyan")
            self.console.print(
                Panel(
                    logo_text,
                    box=box.HEAVY,
                    border_style="cyan",
                    subtitle="长篇小说创作引擎 v5.8",
                    subtitle_align="right",
                )
            )
            self.console.print()
            self.console.print(
                Panel(
                    "[bold]欢迎使用燃灯创作引擎！[/]\n\n"
                    "我来帮你从零开始创建一本小说。\n"
                    "只需要回答几个简单的问题，30 秒就能开写。\n\n"
                    "[dim]随时按 Ctrl+C 取消。[/]",
                    box=box.ROUNDED,
                    border_style="green",
                )
            )
        else:
            print(self.logo())
            print()
            print("  欢迎使用燃灯创作引擎！")
            print("  我来帮你从零开始创建一本小说。")
            print("  只需要回答几个问题，30 秒就能开写。")
            print()

    def _check_project(self) -> bool:
        """检查是否已经在小说项目中"""
        config_path = self.project_root / "novel_config.yaml"
        if config_path.exists():
            if yaml:
                with config_path.open(encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = {}

            existing_id = config.get("novel_id", "")
            self.print(
                f"\n[yellow]⚠ 当前目录已有小说项目: [bold]{existing_id}[/][/]"
                if self.console
                else f"\n  当前目录已有小说项目: {existing_id}"
            )
            if Prompt is not None:
                cont = Confirm.ask("  是否在已有项目中继续？", default=True)
            else:
                cont = input("  是否在已有项目中继续？(Y/n): ").strip().lower() != "n"

            if cont:
                self.print(
                    f"[green]✓ 继续使用已有项目: {existing_id}[/]"
                    if self.console
                    else f"  继续使用已有项目: {existing_id}"
                )
                self.print(
                    "[bold cyan]提示: 输入 randen desk 查看项目状态；"
                    "randen write next 写第一章！[/]"
                    if self.console
                    else "\n  提示: randen write next 写第一章！"
                )
                return False

            # 创建一个新小说？需要确认在同一目录下创建新子项目
            if Prompt is not None:
                create_new = Confirm.ask("  是否在同一目录下创建新小说？", default=False)
            else:
                create_new = input("  是否在同一目录下创建新小说？(y/N): ").strip().lower() == "y"
            if not create_new:
                return False
        return True

    def _ask_title(self) -> str:
        """询问书名，同时作为小说 ID"""
        self.print(
            "\n[bold cyan]📖 你的小说叫什么呢？[/]" if self.console else "\n【书名】你的小说叫什么呢？"
        )
        hint = "例如: 仙王的日常生活、星穹流浪、长安十二时辰"

        if Prompt is not None:
            title = Prompt.ask("  书名", default="我的小说")
        else:
            title = input(f"  书名（{hint}）: ").strip() or "我的小说"

        self.print(
            f"  [green]→ {title}[/]" if self.console else f"  → {title}"
        )
        return title

    def _ask_genre(self) -> str:
        """询问题材"""
        self.print(
            f"\n[bold cyan]🎭 什么题材？[/]" if self.console else "\n【题材】什么题材？"
        )

        if self.console:
            table = Table(box=box.SIMPLE, show_header=False, border_style="dim")
            table.add_column("#", style="dim", width=4)
            table.add_column("题材", style="cyan", width=14)
            # 分两列显示
            mid = (len(GENRES) + 1) // 2
            for i in range(mid):
                left = f"[{i+1}] {GENRES[i]}"
                right_idx = i + mid
                right = f"[{right_idx+1}] {GENRES[right_idx]}" if right_idx < len(GENRES) else ""
                table.add_row(left, right)
            self.console.print(table)
        else:
            for i, g in enumerate(GENRES, 1):
                print(f"  [{i}] {g}")

        if Prompt is not None:
            choice = Prompt.ask("  请选择题材 [1-{}]".format(len(GENRES)), default="1")
        else:
            choice = input(f"  请选择题材 (1-{len(GENRES)}，默认 1): ").strip() or "1"

        try:
            genre = GENRES[int(choice) - 1]
        except (ValueError, IndexError):
            genre = choice  # 接受直接输入

        self.print(
            f"  [green]→ {genre}[/]" if self.console else f"  → {genre}"
        )
        return genre

    def _ask_summary(self) -> str:
        """询问一句话简介"""
        self.print(
            "\n[bold cyan]✍️  一句话简介[/]" if self.console else "\n【简介】一句话简介"
        )
        hint = (
            "一个被退婚的少年，捡到了一块会说话的玉佩……" if self.genre in ("修仙", "东方玄幻")
            else "一个普通程序员，突然发现自己能看见系统的源代码……"
        )

        if Prompt is not None:
            summary = Prompt.ask("  简介", default=hint)
        else:
            summary = input(f"  简介（例如: {hint}）: ").strip() or hint

        self.print(
            f"  [green]→ {summary[:50]}{'...' if len(summary) > 50 else ''}[/]"
            if self.console
            else f"  → {summary[:50]}{'...' if len(summary) > 50 else ''}"
        )
        return summary

    def _check_model(self):
        """检查和引导模型配置"""
        from tools.setup_wizard import load_config

        config = load_config()
        if config and config.get("api_key"):
            self.print(
                "\n[green]✅ AI 模型已配置，可以直接开始创作。[/]"
                if self.console
                else "\n  ✅ AI 模型已配置。"
            )
        else:
            self.print(
                "\n[yellow]⚠ 未检测到 AI 模型配置。需要配置后才能写章节。[/]"
                if self.console
                else "\n  ⚠ 未检测到 AI 模型配置。"
            )
            if Prompt is not None:
                setup_now = Confirm.ask("  是否现在配置？", default=True)
            else:
                setup_now = input("  是否现在配置？(Y/n): ").strip().lower() != "n"

            if setup_now:
                self.print(
                    "\n[bold]启动配置向导...[/]" if self.console else "\n  启动配置向导..."
                )
                from tools.setup_wizard import run_setup_wizard

                run_setup_wizard()
            else:
                self.print(
                    "[yellow]之后可以随时运行 randen setup 来配置。[/]"
                    if self.console
                    else "  之后运行 randen setup 来配置。"
                )

    def _safe_novel_id(self, title: str) -> str:
        """将中文书名转换为安全的英文 ID"""
        text = title.strip()
        if not text:
            return "my_novel"

        # 尝试拼音转换，简化版：直接用下划线连接汉字
        import unicodedata

        safe = []
        for c in text:
            if c.isascii() and c.isalnum():
                safe.append(c.lower())
            elif c in (" ", "-"):
                safe.append("_")
            elif "\u4e00" <= c <= "\u9fff":
                # 保留中文，但用其 unicodedata name 的第一个词
                safe.append(c)  # 直接保留中文
            else:
                safe.append("_")

        result = "".join(safe).strip("_").replace("__", "_")[:48]
        if not result:
            result = "my_novel"

        # 如果有中文，用 pypinyin 转换更好，没有就保留
        has_chinese = any("\u4e00" <= c <= "\u9fff" for c in result)
        if has_chinese:
            # 简单处理：去掉中文，用 novel 后缀
            ascii_only = re.sub(r"[^\x00-\x7f]", "", result).strip("_")
            if ascii_only:
                result = ascii_only
            else:
                result = "novel"

        return result

    def _create_project(self) -> bool:
        """创建项目目录和文件"""
        # 确定 novel_id
        self.novel_id = self._safe_novel_id(self.title)
        self.print(
            f"\n[bold]正在创建项目: [cyan]{self.novel_id}[/] ...[/]"
            if self.console
            else f"\n  创建项目: {self.novel_id} ..."
        )

        try:
            from tools.init_project import init_project

            init_project(self.project_root, self.novel_id, self.title)
        except Exception as e:
            self.print(
                f"\n[red]✗ 项目创建失败: {e}[/]" if self.console else f"\n  ✗ 失败: {e}"
            )
            return False

        # 写入项目元信息 (genre, summary)
        md_path = (
            self.project_root
            / "data"
            / "novels"
            / self.novel_id
            / "src"
            / "story"
            / "background.md"
        )
        if md_path.exists():
            content = md_path.read_text(encoding="utf-8")
            extra = (
                f"\n## 题材\n\n{self.genre}\n\n"
                f"## 一句话简介\n\n{self.summary}\n\n"
            )
            if "一句话故事" in content:
                content = content.replace(
                    "（待填写：主角在什么处境下，为了什么目标，对抗什么阻力。）",
                    f"{self.summary}",
                )
            if "（待填写）" in content:
                content = content.replace("（待填写）", self.genre, 1)
            content += extra
            md_path.write_text(content, encoding="utf-8")

        # 更新 novel_config.yaml 写入标题
        config_path = self.project_root / "novel_config.yaml"
        if config_path.exists() and yaml:
            with config_path.open(encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            if "title" not in cfg or not cfg["title"]:
                cfg["title"] = self.title
            with config_path.open("w", encoding="utf-8") as f:
                yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        return True

    def _show_completion(self):
        """显示完成画面和下一步指引"""
        if self.console:
            self.console.print()
            self.console.rule("[bold green]🎉 项目创建完成！[/]")
            self.console.print()

            # 项目卡片
            info = Table.grid(padding=1)
            info.add_column(style="dim", width=14)
            info.add_column(style="cyan")
            info.add_row("📖 书名", self.title)
            info.add_row("🎭 题材", self.genre)
            info.add_row("🆔 项目 ID", self.novel_id)
            info.add_row("📂 路径", f"data/novels/{self.novel_id}/")
            self.console.print(
                Panel(info, title="📋 项目信息", border_style="cyan", box=box.ROUNDED)
            )

            # 结构卡片
            self.console.print(
                Panel(
                    "[dim]src/[/]          ← 你来编辑的源文件\n"
                    "  ├── outline.md   大纲\n"
                    "  ├── characters/  角色档案\n"
                    "  └── world/       世界观设定\n"
                    "[dim]data/[/]         ← 机器自动生成的运行时数据\n"
                    "  ├── hierarchy.yaml\n"
                    "  ├── characters/cards/\n"
                    "  └── manuscript/  手稿正文",
                    title="📁 项目结构",
                    border_style="blue",
                    box=box.ROUNDED,
                )
            )

            # 下一步
            self.console.print()
            self.console.print(
                Panel(NEXT_STEPS, border_style="green", box=box.ROUNDED)
            )
            self.console.print()
            self.console.print(
                "[bold green]准备好了！输入以下命令写第一章：[/]",
                style="bold",
            )
            self.console.print(
                Syntax(
                    "randen write next",
                    "bash",
                    theme="monokai",
                    padding=1,
                )
            )
            self.console.print(
                "\n[dim]祝创作愉快！🎉[/]" if self.console else "\n  祝创作愉快！"
            )
        else:
            print()
            print("=" * 50)
            print("  🎉 项目创建完成！")
            print("=" * 50)
            print(f"  书名: {self.title}")
            print(f"  题材: {self.genre}")
            print(f"  项目 ID: {self.novel_id}")
            print()
            print("  项目结构:")
            print("    src/")
            print("      ├── outline.md")
            print("      ├── characters/")
            print("      └── world/")
            print("    data/")
            print("      ├── hierarchy.yaml")
            print("      ├── characters/cards/")
            print("      └── manuscript/")
            print()
            print("  下一步：")
            print("    1. randen write next    ← 写第一章！")
            print("    2. randen goethe        ← 和策划编辑聊天")
            print("    3. randen desk          ← 小说工作台")
            print()
            print("  准备好了！输入 randen write next 写第一章 🎉")


def main():
    wizard = InitWizard()
    sys.exit(wizard.run())


if __name__ == "__main__":
    main()
