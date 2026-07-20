"""CLI 格式化输出工具 — 表格、面板、进度条、emoji。

所有终端输出和格式化逻辑集中在此模块。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger("tools.cli")


# ── 通用格式化 ─────────────────────────────────────────────

def show_success(message: str) -> None:
    """显示成功消息"""
    logger.info(f"✅ {message}")


def show_error(message: str, suggestion: str | None = None) -> None:
    """显示错误消息，可选附带建议"""
    logger.error(f"❌ {message}")
    if suggestion:
        logger.info(f"   建议: {suggestion}")


def show_progress(current: int, total: int, label: str = "") -> None:
    """显示进度信息"""
    pct = min(100, round(current / total * 100)) if total else 0
    logger.info(f"⏳ {label}: {current}/{total} ({pct}%)" if label else f"⏳ {current}/{total} ({pct}%)")


# ── 同步状态 ───────────────────────────────────────────────

def print_sync_status(status: dict) -> None:
    """打印同步状态摘要"""
    logger.info(f"同步检查: {status['novel_id']}")
    logger.info(f"  大纲同步待处理: {'是' if status['outline_pending'] else '否'}")
    logger.info(f"  角色档案/卡片: {status['profiles']}/{status['cards']}")
    if status["missing_cards"]:
        logger.info(f"  缺失卡片: {', '.join(status['missing_cards'])}")
    if status.get("stale_cards"):
        logger.info(f"  过期卡片: {', '.join(status['stale_cards'])}")
    if status["extra_cards"]:
        logger.info(f"  额外卡片(可选清理): {', '.join(status['extra_cards'])}")


def build_sync_suggestions(status: dict) -> list[str]:
    """根据同步状态生成下一步建议"""
    messages: list[str] = []

    if status["outline_pending"]:
        messages.append("大纲源文件有更新，运行 `randen sync` 以刷新 data/hierarchy.yaml")

    if status["missing_cards"]:
        preview = ", ".join(status["missing_cards"][:5])
        messages.append(
            f"存在缺失角色卡片（{preview}），运行 `randen sync` "
            "生成 data/characters/cards/*.yaml"
        )

    if status.get("stale_cards"):
        preview = ", ".join(status["stale_cards"][:5])
        messages.append(
            f"存在过期角色卡片（{preview}），运行 `randen sync` "
            "刷新 data/characters/cards/*.yaml"
        )

    if status["extra_cards"]:
        preview = ", ".join(status["extra_cards"][:5])
        messages.append(f"检测到未对应的历史角色卡片（{preview}），可按需手工清理")

    if not messages:
        messages.append("src 与 data 同步状态良好，可直接继续写作")

    return messages


def build_sync_actions(status: dict) -> list[dict[str, str]]:
    """根据同步状态生成可执行动作列表（供 JSON 输出）"""
    actions: list[dict[str, str]] = []

    if status["outline_pending"] or status["missing_cards"] or status.get("stale_cards"):
        actions.append(
            {
                "type": "command",
                "name": "run_sync",
                "command": "randen sync",
                "reason": "将 src 的 outline/characters 同步到 data",
            }
        )

    if status["extra_cards"]:
        actions.append(
            {
                "type": "manual",
                "name": "review_extra_cards",
                "reason": "存在未对应档案的历史卡片，按需清理 data/characters/cards/*.yaml",
            }
        )

    if not actions:
        actions.append(
            {
                "type": "noop",
                "name": "continue_writing",
                "reason": "src 与 data 已同步，可直接继续写作流程",
            }
        )

    return actions


def output_sync_json_result(mode: str, status: dict, suggestions: list[str],
                            actions: list[dict], exit_code: int,
                            before: dict | None = None) -> None:
    """以 JSON 格式输出同步结果"""
    import json as _json
    payload: dict = {
        "mode": mode,
        "status" if mode == "check" else "after": status,
        "suggestions": suggestions,
        "actions": actions,
        "ok": not status["needs_sync"],
        "exit_code": exit_code,
    }
    if mode == "check":
        payload["status"] = payload.pop("status" if mode == "check" else "after")
    else:
        payload["after"] = payload.pop("status" if mode == "check" else "after")
    if before is not None:
        payload["before"] = before
    # Fix up key names
    if mode == "check":
        payload_final = {
            "mode": mode,
            "status": status,
            "suggestions": suggestions,
            "actions": actions,
            "ok": not status["needs_sync"],
            "exit_code": exit_code,
        }
    else:
        payload_final = {
            "mode": mode,
            "before": before,
            "after": status,
            "suggestions": suggestions,
            "actions": actions,
            "ok": not status["needs_sync"],
            "exit_code": exit_code,
        }
    print(_json.dumps(payload_final, ensure_ascii=False, indent=2))


# ── 市场雷达 ───────────────────────────────────────────────

def print_market_radar(result: dict, output_path: str | None = None) -> None:
    """打印市场分析结果"""
    print("\n" + "=" * 50)
    print("   市场分析结果")
    print("=" * 50)
    for index, item in enumerate(result["recommendations"], 1):
        print(
            f"\n{index}. [{float(item['confidence']):.0%}] "
            f"{item['platform']}/{item['genre']}"
        )
        print(f"   创意: {item['concept']}")
        print(f"   理由: {item['reasoning']}")
        if item["benchmarks"]:
            print(f"   参考: {', '.join(item['benchmarks'][:3])}")
    if result["trends"]:
        print("\n" + "-" * 50)
        print("趋势:")
        for trend in result["trends"]:
            print(f"  - {trend}")

    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        sections = ["# 市场分析结果", ""]
        for item in result["recommendations"]:
            sections.append(
                f"## {item['platform']}/{item['genre']}\n\n"
                f"- 置信度: {float(item['confidence']):.0%}\n"
                f"- 创意: {item['concept']}\n"
                f"- 理由: {item['reasoning']}\n"
            )
        output.write_text("\n".join(sections), encoding="utf-8")
        print(f"\n已保存到: {output}")


# ── 工作台 ─────────────────────────────────────────────────

def print_desk(snapshot: object) -> None:
    """打印小说专用终端工作台"""
    width = 66
    target = snapshot.target_units
    percent = min(100, round(snapshot.writing_units / target * 100)) if target else 0
    filled = round(percent / 5)
    progress = "#" * filled + "-" * (20 - filled)
    readiness_labels = {
        "author_intent": "作者意图",
        "background": "故事背景",
        "foundation": "基础设定",
        "characters": "主要人物",
        "outline": "可写大纲",
        "creative_focus": "创作罗盘",
    }

    print("=" * width)
    print(f"  RANDEN  /  {snapshot.title}")
    print("  长篇小说创作工作台")
    print("=" * width)
    print(
        f"  进度  [{progress}] {percent:>3}%   "
        f"{snapshot.chapters} 章 / {snapshot.writing_units:,} 字"
    )
    print(
        f"  当前  {snapshot.current_arc} · {snapshot.current_chapter}   "
        f"阶段: {snapshot.stage}"
    )
    print(
        f"  资产  {snapshot.characters} 人物 · {snapshot.world_documents} 设定文档 · "
        f"{snapshot.pending_foreshadowing} 待处理伏笔"
    )
    print(
        f"  质量  {snapshot.reviewed_chapters} 章已审 · "
        f"均分 {snapshot.average_review_score:.1f} · {snapshot.total_tokens:,} tokens"
    )
    print("-" * width)
    print("  创作罗盘")
    goal = snapshot.creative_focus.goal or "尚未设置；先明确这一阶段最重要的叙事目标。"
    print(f"  {goal[: width - 4]}")
    if snapshot.creative_focus.must_keep:
        print(f"  必须保留: {'；'.join(snapshot.creative_focus.must_keep)[: width - 12]}")
    if snapshot.creative_focus.must_avoid:
        print(f"  必须避免: {'；'.join(snapshot.creative_focus.must_avoid)[: width - 12]}")
    print("-" * width)
    readiness = "  ".join(
        f"[{'OK' if snapshot.readiness[key] else '--'}] {label}"
        for key, label in readiness_labels.items()
    )
    for start in range(0, len(readiness), width - 2):
        print(f"  {readiness[start:start + width - 2]}")
    print("-" * width)
    print("  下一步")
    for action in snapshot.next_actions:
        print(f"  > {action}")
    print("=" * width)


def print_desk_json(snapshot: object) -> None:
    """以 JSON 格式输出工作台状态"""
    import json as _json
    print(_json.dumps(snapshot.to_dict(), ensure_ascii=False, indent=2))


# ── 状态 ───────────────────────────────────────────────────

def print_status(project_root: Path) -> None:
    """打印项目状态"""
    from tools.agent.tool_runtime import build_tool_executors

    status = build_tool_executors(project_root)["get_status"]({})
    logger.info(f"项目: {status['novel_id']}")
    logger.info(f"当前篇: {status['current_arc']}")
    logger.info(f"当前章: {status['current_chapter']}")
    logger.info(f"已写章节: {status['chapters_written']}")
    logger.info(f"快照数: {status['snapshots']}")


def print_status_json(project_root: Path) -> None:
    """以 JSON 格式输出项目状态"""
    import json as _json
    from tools.novel_service import NovelApplicationService, NovelServiceError

    try:
        service = NovelApplicationService(project_root)
        print(_json.dumps(
            service.workspace_snapshot(),
            ensure_ascii=False,
            indent=2,
        ))
    except NovelServiceError as exc:
        logger.error(str(exc))


# ── 上下文 ─────────────────────────────────────────────────

def print_context_preview(preview: dict) -> None:
    """打印上下文预览"""
    sections = preview["packet"].get("prompt_sections", {})
    logger.info(f"上下文 ({len(sections)} 个段落):")
    for name in sections:
        logger.info(f"  - {name}")
