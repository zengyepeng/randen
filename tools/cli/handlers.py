"""CLI 命令处理器 — 委托给 NovelApplicationService 或直接调用 tools/。

每个 handle_* 函数负责：参数检查 → 委托服务 → 调用 display 输出 → 返回退出码
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from tools.cli.display import (
    build_sync_actions, build_sync_suggestions, output_sync_json_result,
    print_context_preview, print_desk, print_desk_json,
    print_market_radar, print_sync_status, print_status, print_status_json,
)
from tools.cli.validators import load_novel_config, resolve_novel_id, validate_model_config, validate_port

logger = logging.getLogger(__name__)
_NSE = None  # lazy import cache for NovelServiceError


def _get_nse():
    """延迟导入 NovelServiceError，避免循环依赖"""
    global _NSE
    if _NSE is None:
        from tools.novel_service import NovelServiceError as _NSE
    return _NSE


# ── 22 个命令处理器 ───────────────────────────────────────

def handle_init(args) -> int:
    """初始化项目"""
    if not args.novel_id:
        from tools.init_wizard import InitWizard
        return InitWizard().run()
    from tools.novel_service import NovelApplicationService
    logger.info(f"初始化项目: {args.novel_id}")
    if getattr(args, "template", "default") != "default":
        logger.info("当前仅支持 default 模板，已按默认模板初始化。")
    try:
        NovelApplicationService.initialize(Path.cwd(), args.novel_id)
        return 0
    except _get_nse() as exc:
        logger.error(str(exc))
        return 1


def handle_setup(_args) -> int:
    """运行 AI 模型配置向导"""
    from tools.setup_wizard import run_setup_wizard
    return run_setup_wizard()


def handle_goethe(_args) -> int:
    """Goethe 长期会话规划入口"""
    from tools.goethe import run_goethe
    return run_goethe()


def handle_dante(_args) -> int:
    """Dante 长会话主入口"""
    try:
        from tools.agent.dante import run_dante
        return run_dante()
    except ImportError as e:
        logger.error(f"Dante 模块未安装: {e}")
        return 1
    except Exception as e:
        logger.error(f"Dante 启动失败: {e}")
        return 1


def handle_sync(args) -> int:
    """同步 src -> data（outline/character）"""
    from tools.novel_service import NovelApplicationService
    project_root = Path.cwd()
    try:
        service = NovelApplicationService(project_root)
    except _get_nse() as exc:
        logger.error(str(exc))
        return 1

    if args.novel_id and args.novel_id not in {"current", service.novel_id}:
        logger.error("--novel-id 必须与当前 novel_config.yaml 一致")
        return 1

    before = service.sync_status()
    suggestions = build_sync_suggestions(before)
    before_actions = build_sync_actions(before)
    if not args.json:
        print_sync_status(before)
        for msg in suggestions:
            logger.info(f"  建议: {msg}")

    if args.check:
        code = 2 if before["needs_sync"] else 0
        if args.json:
            output_sync_json_result("check", before, suggestions, before_actions, code)
        elif before["needs_sync"]:
            logger.warning("检测到未同步项（仅检查模式，未执行写入）")
        else:
            logger.info("同步状态正常")
        return code

    try:
        after = service.sync()["after"]
    except _get_nse() as exc:
        logger.error(str(exc))
        return 1
    after_suggestions = build_sync_suggestions(after)
    after_actions = build_sync_actions(after)
    code = 0 if not after["needs_sync"] else 1

    if args.json:
        output_sync_json_result("apply", after, after_suggestions, after_actions, code, before=before)
        return code
    print_sync_status(after)
    for msg in after_suggestions:
        logger.info(f"  建议: {msg}")
    if after["needs_sync"]:
        logger.warning("同步执行后仍存在未同步项，请检查输入文件格式")
    else:
        logger.info("同步完成")
    return code


def handle_write(args) -> int:
    """写章节"""
    from tools.novel_service import NovelApplicationService
    service = None; chapter = str(args.chapter)
    try:
        service = NovelApplicationService(Path.cwd())
        chapter = service.resolve_chapter_id(args.chapter)
        logger.info(f"写章节: {chapter}")
        result = service.write_chapter({"chapter_id": chapter, "guidance": "",
                                        "target_words": 0, "temperature": args.temperature})
    except _get_nse() as exc:
        logger.error(str(exc))
        if getattr(args, "show", False) and service is not None:
            try: print(str(service.context_preview(chapter).get("markdown") or ""))
            except _get_nse(): pass
        return 1
    logger.info(f"章节已生成: {result.get('title', '')}")
    logger.info(f"字数: {result.get('word_count', 0)}")
    truth_updates = result.get("truth_updates", {})
    if truth_updates:
        logger.info(f"真相文件已更新: {', '.join(truth_updates.keys())}")
    else:
        logger.info("本章未产生可写入的真相增量")
    return 0


def handle_multi_write(args) -> int:
    """使用统一章节管线执行多 Agent 写作"""
    from tools.novel_service import NovelApplicationService
    try:
        result = NovelApplicationService(Path.cwd()).multi_write({
            "chapter_id": args.chapter, "temperature": args.temperature,
            "no_review": bool(args.no_review), "show_packet": bool(args.show_packet),
            "packet_output_dir": args.packet_output_dir})
    except _get_nse() as exc:
        logger.error(str(exc)); return 1
    if result.get("packet_path"): logger.info(f"组装包快照: {result['packet_path']}")
    if result.get("packet_markdown"): print(result["packet_markdown"])
    logger.info(f"章节已保存: {result['chapter_id']}")
    review = result.get("review")
    if isinstance(review, dict):
        logger.info(f"审查得分: {float(review.get('score', 0)):.0f}/100")
        logger.info(f"审查问题数: {int(review.get('issues', 0))}")
    updates = result.get("applied_state_updates") or {}
    if isinstance(updates, dict) and updates: logger.info(f"已更新状态文件: {', '.join(updates)}")
    concepts = result.get("new_concepts") or []
    if isinstance(concepts, list) and concepts: logger.info(f"已新增概念文档: {', '.join(str(c) for c in concepts)}")
    return 0


def handle_review(args) -> int:
    """审查章节"""
    from tools.novel_service import NovelApplicationService
    try:
        service = NovelApplicationService(Path.cwd())
        chapter = service.resolve_chapter_id(args.chapter, latest=True)
        logger.info(f"审查章节: {chapter}")
        result = service.review_chapter(chapter)
    except _get_nse() as exc: logger.error(str(exc)); return 1
    logger.info(f"审查结果: {'通过' if result.get('passed') else '未通过'}")
    logger.info(f"得分: {float(result.get('score', 0)):.0f}/100")
    logger.info(f"问题数: {int(result.get('issues', 0))}")
    return 0


def handle_context(args) -> int:
    """构建上下文"""
    from tools.novel_service import NovelApplicationService
    try:
        preview = NovelApplicationService(Path.cwd()).context_preview(args.chapter)
    except _get_nse() as exc: logger.error(str(exc)); return 1
    if args.show: print(preview["markdown"])
    else: print_context_preview(preview)
    return 0


def handle_assemble(args) -> int:
    """按 V2 规则组装章节上下文包"""
    from tools.novel_service import NovelApplicationService
    project_root = Path.cwd()
    try:
        service = NovelApplicationService(project_root)
        chapter = service.resolve_chapter_id(args.chapter)
        packet = service.assemble_packet(chapter)
    except _get_nse() as exc: logger.error(str(exc)); return 1

    rendered = (json.dumps(packet, ensure_ascii=False, indent=2) if args.format == "json"
                else str(packet.get("outline") or ""))
    ext = "json" if args.format == "json" else "md"

    target_dir = (Path(args.output_dir) if args.output_dir
                  else _get_test_output_dir(project_root, service.novel_id, "context_packets"))
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (target_dir / f"{chapter}_{stamp}.{ext}").write_text(rendered, encoding="utf-8")
    logger.info(f"组装结果快照: {target_dir / f'{chapter}_{stamp}.{ext}'}")
    if args.output:
        p = Path(args.output); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(rendered, encoding="utf-8")
        logger.info(f"组装结果已输出: {p}")
    if not args.no_print and not args.output: print(rendered)
    return 0


def handle_style(args) -> int:
    """风格管理"""
    if args.style_action == "extract": return _run_source_extract(args, focus="style")
    if args.style_action == "synthesize": return _handle_style_synthesize(args)
    logger.error("请指定 style 子命令: extract, synthesize"); return 1


def _handle_style_synthesize(args) -> int:
    """合成作品级风格文档"""
    from tools.novel_service import NovelApplicationService
    project_root = Path.cwd(); config = load_novel_config(project_root)
    if not config and getattr(args, "novel_id", "current") == "current":
        logger.error("未找到 novel_config.yaml，请先运行 randen init"); return 1
    novel_id = (config.get("novel_id", "") if getattr(args, "novel_id", "current") == "current"
                else getattr(args, "novel_id", ""))
    if not novel_id: logger.error("无法确定 novel_id"); return 1
    style_id = config.get("style_id", novel_id) if config else novel_id
    try:
        result = NovelApplicationService(project_root).synthesize_style(style_id)
    except _get_nse() as exc: logger.error(str(exc)); return 1
    logger.info(f"合成风格文档已写入: {result['composed_path']} (mode={result['mode']})")
    return 0


def handle_setting(args) -> int:
    """设定来源管理"""
    if args.setting_action == "extract": return _run_source_extract(args, focus="setting")
    logger.error("请指定 setting 子命令: extract"); return 1


def handle_source(args) -> int:
    """来源文本 source pack 管理"""
    if args.source_action == "review": return _handle_source_review(args)
    if args.source_action == "promote": return _handle_source_promote(args)
    logger.error("请指定 source 子命令: review, promote"); return 1


def _handle_source_review(args) -> int:
    """审阅 source pack"""
    from tools.novel_service import NovelApplicationService
    project_root = Path.cwd()
    novel_id = resolve_novel_id(project_root, getattr(args, "novel_id", "current"))
    if not novel_id: logger.error("未找到 novel_config.yaml，请指定 --novel-id"); return 1
    try: result = NovelApplicationService(project_root).review_source(args.source_id)
    except _get_nse() as exc: logger.error(str(exc)); return 1
    print(result["review_report"]); return 0


def _handle_source_promote(args) -> int:
    """晋升 source pack"""
    from tools.novel_service import NovelApplicationService
    project_root = Path.cwd()
    novel_id = resolve_novel_id(project_root, getattr(args, "novel_id", "current"))
    if not novel_id: logger.error("未找到 novel_config.yaml，请指定 --novel-id"); return 1
    try: NovelApplicationService(project_root).promote_source(args.source_id, args.target)
    except _get_nse() as exc: logger.error(str(exc)); return 1
    logger.info(f"source promote 完成: {args.source_id} -> {args.target}"); return 0


def handle_radar(args) -> int:
    """运行小说市场分析并渲染结果"""
    from tools.novel_service import NovelApplicationService
    try: result = NovelApplicationService(Path.cwd()).market_radar(platforms=args.platform, top_n=args.top)
    except _get_nse() as exc: logger.error(str(exc)); return 1
    print_market_radar(result, output_path=args.output); return 0


def handle_status(args) -> int:
    """查看状态"""
    from tools.novel_service import NovelApplicationService
    project_root = Path.cwd()
    try: NovelApplicationService(project_root)
    except _get_nse() as exc: logger.error(str(exc)); return 1
    if getattr(args, "json", False): print_status_json(project_root)
    else: print_status(project_root)
    return 0


def handle_focus(args) -> int:
    """查看或更新近期创作罗盘"""
    from tools.novel_service import NovelApplicationService
    action = getattr(args, "focus_action", None) or "show"
    try:
        service = NovelApplicationService(Path.cwd())
        if action == "set":
            path = service.update_focus(goal=args.goal, must_keep=args.keep,
                                        must_avoid=args.avoid, notes=args.note)
            logger.info(f"创作罗盘已更新: {path}")
            logger.info("后续章节上下文会优先携带这些约束"); return 0
        if action == "clear": service.clear_focus(); logger.info("创作罗盘已清空"); return 0
        print(service.render_focus())
    except _get_nse() as exc: logger.error(str(exc)); return 1
    return 0


def handle_import(args) -> int:
    """导入已有 TXT/Markdown 小说正文"""
    from tools.novel_service import NovelApplicationService
    try:
        result = NovelApplicationService(Path.cwd()).import_book(
            Path(args.source).expanduser(), arc_id=args.arc,
            start_number=args.start, force=bool(args.force))
    except _get_nse() as exc: logger.error(f"导入失败: {exc}"); return 1
    logger.info(f"已导入 {len(result['imported'])} 章到 {result['arc_id']}")
    logger.info(f"合计字数: {result['writing_units']}")
    logger.info(f"下一章: {result['next_chapter']}"); return 0


def handle_export(args) -> int:
    """导出完整小说正文"""
    from tools.novel_service import NovelApplicationService
    project_root = Path.cwd()
    try: service = NovelApplicationService(project_root)
    except _get_nse() as exc: logger.error(str(exc)); return 1
    fmt = args.format
    output = (Path(args.output).expanduser() if args.output
              else project_root / "exports" / f"{service.novel_id}.{fmt}")
    try: path = service.export_book(output, format_name=fmt, title=args.title)
    except _get_nse() as exc: logger.error(f"导出失败: {exc}"); return 1
    logger.info(f"整书已导出: {path}"); return 0


def handle_desk(args) -> int:
    """显示小说专用终端工作台"""
    from tools.novel_service import NovelApplicationService
    try: snapshot = NovelApplicationService(Path.cwd()).workspace_state()
    except _get_nse() as exc: logger.error(str(exc)); return 1
    if getattr(args, "json", False): print_desk_json(snapshot)
    else: print_desk(snapshot)
    return 0


def handle_studio(args) -> int:
    """启动仅绑定本机回环地址的 Studio"""
    from tools.studio import StudioError, run_studio
    if not validate_port(args.port):
        logger.error("端口必须在 0 到 65535 之间"); return 1
    try: return run_studio(Path.cwd(), port=args.port, open_browser=not bool(args.no_open))
    except (OSError, StudioError) as exc: logger.error(f"Studio 启动失败: {exc}"); return 1


def handle_doctor(_args) -> int:
    """环境与路径自检"""
    project_root = Path.cwd(); config = load_novel_config(project_root)
    if not config: logger.error("未找到 novel_config.yaml"); return 1
    novel_id = config.get("novel_id", "unknown")
    novel_root = project_root / "data" / "novels" / novel_id
    src_root = novel_root / "src"; runtime_root = novel_root / "data"
    logger.info(f"工作目录: {project_root}")
    logger.info(f"小说 ID: {novel_id}")
    logger.info(f"源目录: {src_root} ({'存在' if src_root.exists() else '缺失'})")
    logger.info(f"运行目录: {runtime_root} ({'存在' if runtime_root.exists() else '缺失'})")
    logger.info(f"测试输出目录: {_get_test_output_dir(project_root, novel_id, 'context_packets')}")
    model_info = validate_model_config()
    logger.info(f"LLM_PROVIDER: {model_info['provider'] or '<缺失>'}")
    logger.info(f"LLM_MODEL: {model_info['model'] or '<缺失>'}")
    logger.info(f"LLM_API_KEY: {model_info['api_key_masked']}"); return 0


def handle_agent(_args) -> int:
    """agent 命令 - 已退役"""
    logger.error("randen agent 已退役，请改用 randen dante。")
    return 1


# ── 内部辅助 ───────────────────────────────────────────────

def _run_source_extract(args, *, focus: str) -> int:
    """从用户提供文本提取 source pack"""
    from tools.novel_service import NovelApplicationService
    source_file = Path(args.source)
    if not source_file.exists(): logger.error(f"源文件不存在: {source_file}"); return 1
    try:
        NovelApplicationService(Path.cwd()).extract_source(
            source_id=args.source_id, source_file=source_file,
            focus=focus, chunk_size=args.chunk_size)
    except _get_nse() as exc: logger.error(str(exc)); return 1
    return 0


def _get_test_output_dir(project_root: Path, novel_id: str, category: str) -> Path:
    """获取测试输出目录"""
    return project_root / "data" / "novels" / novel_id / "data" / "test_outputs" / category
