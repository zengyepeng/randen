#!/usr/bin/env python3
"""燃灯配置向导 — setup 命令

交互式 LLM 配置向导，引导用户配置 AI 模型提供商。
保存到 ~/.randen/config.yaml
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich import box
except ImportError:
    # 降级为纯文本
    Console = None

try:
    import yaml
except ImportError:
    yaml = None

CONFIG_DIR = Path.home() / ".randen"
CONFIG_PATH = CONFIG_DIR / "config.yaml"

# 支持的 AI 提供商
PROVIDERS = [
    {
        "id": "openai",
        "name": "OpenAI",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1-mini", "o3-mini"],
        "default_model": "gpt-4o-mini",
        "default_url": "https://api.openai.com/v1",
        "docs_url": "https://platform.openai.com/api-keys",
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "default_model": "deepseek-chat",
        "default_url": "https://api.deepseek.com/v1",
        "docs_url": "https://platform.deepseek.com/api_keys",
    },
    {
        "id": "zhipu",
        "name": "智谱 AI (GLM)",
        "models": [
            "glm-4-plus",
            "glm-4-flash",
            "glm-4-air",
            "glm-4v-flash",
            "glm-4-long",
        ],
        "default_model": "glm-4-flash",
        "default_url": "https://open.bigmodel.cn/api/paas/v4",
        "docs_url": "https://bigmodel.cn/usercenter/apikeys",
    },
    {
        "id": "anthropic",
        "name": "Anthropic (Claude)",
        "models": ["claude-sonnet-4-20250514", "claude-haiku-4-20250514", "claude-opus-4-20250514"],
        "default_model": "claude-haiku-4-20250514",
        "default_url": "https://api.anthropic.com",
        "docs_url": "https://console.anthropic.com/settings/keys",
    },
    {
        "id": "moonshot",
        "name": "Moonshot (Kimi)",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "default_model": "moonshot-v1-32k",
        "default_url": "https://api.moonshot.cn/v1",
        "docs_url": "https://platform.moonshot.cn/console/api-keys",
    },
    {
        "id": "dashscope",
        "name": "阿里百炼 (Qwen)",
        "models": [
            "qwen-max",
            "qwen-plus",
            "qwen-turbo",
            "qwen2.5-72b-instruct",
        ],
        "default_model": "qwen-plus",
        "default_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "docs_url": "https://bailian.console.aliyun.com/",
    },
    {
        "id": "qianfan",
        "name": "百度千帆 (ERNIE)",
        "models": [
            "ernie-4.0-turbo-8k",
            "ernie-3.5-8k",
            "ernie-speed-8k",
            "deepseek-v3",
        ],
        "default_model": "ernie-speed-8k",
        "default_url": "https://qianfan.baidubce.com/v2",
        "docs_url": "https://console.bce.baidu.com/qianfan/ais/console/applicationConsole/application",
    },
    {
        "id": "volcengine",
        "name": "火山引擎 (豆包)",
        "models": [
            "doubao-pro-32k",
            "doubao-lite-32k",
            "deepseek-r1-250120",
            "deepseek-v3-250324",
        ],
        "default_model": "doubao-pro-32k",
        "default_url": "https://ark.cn-beijing.volces.com/api/v3",
        "docs_url": "https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey",
    },
    {
        "id": "siliconflow",
        "name": "SiliconFlow (硅基流动)",
        "models": [
            "deepseek-ai/DeepSeek-V3",
            "deepseek-ai/DeepSeek-R1",
            "Qwen/Qwen2.5-72B-Instruct",
            "Qwen/Qwen2.5-32B-Instruct",
        ],
        "default_model": "deepseek-ai/DeepSeek-V3",
        "default_url": "https://api.siliconflow.cn/v1",
        "docs_url": "https://cloud.siliconflow.cn/account/ak",
    },
    {
        "id": "custom",
        "name": "自定义 OpenAI 兼容接口",
        "models": ["自行输入"],
        "default_model": "",
        "default_url": "http://localhost:11434/v1",
        "docs_url": "",
    },
]


def _plain_print(text: str, style: str = "info"):
    """纯文本降级输出"""
    prefix = {"info": "ℹ", "success": "✓", "warn": "⚠", "error": "✗", "prompt": "?"}.get(
        style, "•"
    )
    print(f"  {prefix} {text}")


def _make_console():
    if Console:
        return Console()
    return None


def _rich_print(console):
    """适配 Rich console.print，忽略不支持的 style 参数"""
    def _print(text, style=None, **kwargs):
        return console.print(text)
    return _print


def _show_banner(console):
    banner = (
        "[bold cyan]"
        "   ╭─────────────────────────╮\n"
        "   │      燃  灯  配  置      │\n"
        "   │    AI 模型连接向导      │\n"
        "   ╰─────────────────────────╯[/]"
    )
    if console:
        console.print(Panel(banner, box=box.ROUNDED, border_style="cyan"))
    else:
        print("")
        print("   ╭─────────────────────────╮")
        print("   │      燃  灯  配  置      │")
        print("   │    AI 模型连接向导      │")
        print("   ╰─────────────────────────╯")
        print("")


def load_config() -> dict | None:
    """加载已有配置"""
    if CONFIG_PATH.exists():
        if yaml:
            with CONFIG_PATH.open(encoding="utf-8") as f:
                return yaml.safe_load(f)
        else:
            import json

            with CONFIG_PATH.open(encoding="utf-8") as f:
                return json.load(f)
    # 也检查环境变量
    env_config = {}
    for key in ("LLM_PROVIDER", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
        val = os.environ.get(key)
        if val:
            env_config[key.lower().replace("llm_", "")] = val
    return env_config if env_config else None


def save_config(config: dict):
    """保存配置（包含所有字段但保持人性化可读）"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # 按友好顺序排列
    ordered = {
        "provider": config.get("provider", ""),
        "model": config.get("model", ""),
        "base_url": config.get("base_url", ""),
        "api_key": "",
    }

    # 保留额外的字段
    for k, v in config.items():
        if k not in ordered:
            ordered[k] = v

    raw = config.get("api_key", "")
    if raw:
        ordered["api_key"] = raw

    if yaml:
        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            yaml.dump(ordered, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    else:
        import json

        with CONFIG_PATH.open("w", encoding="utf-8") as f:
            json.dump(ordered, f, ensure_ascii=False, indent=2)
    return CONFIG_PATH


def test_connection(provider: str, base_url: str, api_key: str, model: str) -> tuple[bool, str]:
    """测试 LLM 连接"""
    print(f"   正在测试连接 (模型: {model})...", end=" ", flush=True)
    try:
        import openai

        client = openai.OpenAI(api_key=api_key, base_url=base_url, timeout=15)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "回复「连接成功」四个字即可，不要多说。"}],
            max_tokens=20,
            temperature=0.1,
        )
        content = response.choices[0].message.content or ""
        return True, f"连接成功！模型回复: {content.strip()}"
    except Exception as e:
        return False, f"连接失败: {str(e)}"


def run_setup_wizard() -> int:
    """运行配置向导"""
    console = _make_console()

    _show_banner(console)
    _print = _rich_print(console) if console else _plain_print

    existing = load_config()
    if existing:
        masked_key = ""
        raw = existing.get("api_key") or os.environ.get("LLM_API_KEY", "")
        if raw:
            masked_key = f"{raw[:8]}...{raw[-4:]}" if len(raw) > 12 else "***"
        _print(
            Panel(
                f"[green]检测到已有配置[/]\n"
                f"  提供商: {existing.get('provider', '?')}\n"
                f"  模型: {existing.get('model', '?')}\n"
                f"  API Key: {masked_key or '未设置'}\n"
                f"  地址: {existing.get('base_url', '未设置')}",
                title="📋 当前配置",
                border_style="green",
            )
            if console
            else f"\n  当前配置:\n    提供商: {existing.get('provider', '?')}\n    模型: {existing.get('model', '?')}\n    API Key: {masked_key or '未设置'}\n    地址: {existing.get('base_url', '未设置')}",
            style="info" if _print is _plain_print else None,
        )

        if Prompt is not None:
            reconfirm = Confirm.ask("  是否重新配置？", default=False)
        else:
            reconfirm = input("  是否重新配置？(y/N): ").strip().lower() == "y"

        if not reconfirm:
            _print("[green]✓ 保持现有配置[/]", style="success")
            return 0

    # ── 步骤 1: 选择提供商 ──────────────────────────
    _print("\n[bold]步骤 1: 选择 AI 提供商[/]" if console else "\n【步骤 1】选择 AI 提供商", style="info")

    if console:
        table = Table(box=box.SIMPLE, show_header=False, border_style="dim")
        table.add_column("#", style="dim", width=4)
        table.add_column("提供商", style="cyan")
        table.add_column("默认模型", style="yellow")
        table.add_column("参考文档", style="blue")
        for i, p in enumerate(PROVIDERS, 1):
            table.add_row(str(i), p["name"], p["default_model"], p["docs_url"])
        console.print(table)
    else:
        for i, p in enumerate(PROVIDERS, 1):
            print(f"  [{i}] {p['name']} — 默认: {p['default_model']}")

    if Prompt is not None:
        choice = Prompt.ask(
            "  请选择 [1-{}]".format(len(PROVIDERS)),
            default="1",
            show_choices=False,
        )
    else:
        choice = input(f"  请选择 (1-{len(PROVIDERS)}，默认 1): ").strip() or "1"

    try:
        provider = PROVIDERS[int(choice) - 1]
    except (ValueError, IndexError):
        _print("[red]无效选择，使用 OpenAI[/]", style="error")
        provider = PROVIDERS[0]

    # ── 步骤 2: API Key ────────────────────────────
    _print(
        f"\n[bold]步骤 2: 输入 {provider['name']} API Key[/]" if console else f"\n【步骤 2】输入 {provider['name']} API Key",
        style="info",
    )
    _print(
        f"  获取方式: {provider['docs_url']}" if console else f"  获取方式: {provider['docs_url']}",
        style="info" if console else "info",
    )

    if Prompt is not None:
        _print("  API Key（输入时光标不动是正常的，盲打即可）")
        api_key = Prompt.ask("  API Key", password=True).strip()
    else:
        import getpass
        api_key = getpass.getpass("  API Key（输入不可见，正常现象）: ").strip()

    if not api_key:
        _print("[yellow]⚠ Key 为空，后续将无法调用 AI。可用 randen setup 重新配置。[/]", style="warn")

    # ── 步骤 3: base_url ───────────────────────────
    _print(
        f"\n[bold]步骤 3: API 地址（直接回车使用默认值）[/]" if console else "\n【步骤 3】API 地址",
        style="info",
    )

    if Prompt is not None:
        base_url = Prompt.ask(
            "  API 地址",
            default=provider["default_url"],
        ).strip()
    else:
        raw = input(f"  API 地址 (默认 {provider['default_url']}): ").strip()
        base_url = raw if raw else provider["default_url"]

    # ── 步骤 4: 模型 ──────────────────────────────
    _print(
        f"\n[bold]步骤 4: 选择模型[/]" if console else "\n【步骤 4】选择模型",
        style="info",
    )

    if console:
        model_table = Table(box=box.SIMPLE, show_header=False, border_style="dim")
        model_table.add_column("#", style="dim", width=4)
        model_table.add_column("模型名", style="cyan")
        for i, m in enumerate(provider["models"], 1):
            model_table.add_row(str(i), m)
        console.print(model_table)
    else:
        for i, m in enumerate(provider["models"], 1):
            print(f"  [{i}] {m}")

    if Prompt is not None:
        model_choice = Prompt.ask(
            "  请选择 [1-{}] 或直接输入模型名称".format(len(provider["models"])),
            default="1",
        ).strip()
    else:
        model_choice = input(f"  请选择 (1-{len(provider['models'])}，默认 1): ").strip() or "1"

    try:
        idx = int(model_choice)
        model = provider["models"][idx - 1]
    except (ValueError, IndexError):
        # 用户直接输入了模型名
        model = model_choice if model_choice else provider["default_model"]

    # ── 步骤 5: 测试连接 ───────────────────────────
    _print(
        f"\n[bold]步骤 5: 测试连接[/]" if console else "\n【步骤 5】测试连接",
        style="info",
    )

    if api_key:
        test_choice = "y"
        if Prompt is not None:
            test_choice = Confirm.ask("  是否测试连接？", default=True)
        else:
            test_input = input("  是否测试连接？(Y/n): ").strip().lower()
            test_choice = "n" if test_input == "n" else "y"

        if test_choice == "y" or test_choice is True:
            success, msg = test_connection(
                provider["id"], base_url, api_key, model
            )
            if console:
                console.print(
                    Panel(
                        msg,
                        border_style="green" if success else "red",
                        title="连接测试",
                    )
                )
            else:
                _print(msg, "success" if success else "error")

            if not success and Prompt is not None:
                retry = Confirm.ask("  是否重试或修改配置？", default=True)
                if retry:
                    _print("[yellow]请重新运行 randen setup[/]", style="warn")
                    return 1
    else:
        _print("[yellow]⚠ 跳过连接测试（API Key 为空）[/]", style="warn")

    # ── 保存 ──────────────────────────────────────
    config = {
        "provider": provider["id"],
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
    }

    path = save_config(config)
    _print(
        Panel(
            f"[green]配置已保存到:[/] {path}\n\n"
            f"  提供商: {provider['name']}\n"
            f"  模型: {model}\n"
            f"  地址: {base_url}",
            title="✅ 配置完成",
            border_style="green",
        )
        if console
        else f"\n✅ 配置完成\n  配置文件: {path}\n  提供商: {provider['name']}\n  模型: {model}\n  地址: {base_url}",
        style="success",
    )

    _print(
        "[bold cyan]🎉 现在可以创建你的第一本书了！运行: randen init[/]" if console else "\n🎉 现在可以创建你的第一本书了！运行 randen init",
        style="info",
    )

    return 0


def main():
    sys.exit(run_setup_wizard())


if __name__ == "__main__":
    main()
