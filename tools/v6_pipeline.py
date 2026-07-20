"""燃灯 — v6.0 全栈工业化写作流水线

统一编排所有 v6.0 模块，实现端到端自动化：
    1. 加载大纲 → 多模型路由
    2. RAG 素材检索
    3. 状态加载（压缩记忆 + Canonical Packet）
    4. 谈判预处理（可选）
    5. 正文生成（状态机）
    6. 原创性雷达自检 → 不达标自动重写
    7. AI 痕迹脱敏（四步法）
    8. 状态更新 + 写入草稿箱

对应 v6.0 规格书 Pipeline 章节的完整实现。
"""

from __future__ import annotations

import os
import json
import re
from pathlib import Path
from typing import Any

# ═══════════════════════════════════════════════════════════
# 模型路由
# ═══════════════════════════════════════════════════════════

def _route_model(task: str) -> str:
    """根据任务类型路由到最合适的模型。"""
    try:
        import yaml
        config_path = Path(__file__).parent.parent / "config" / "model_router_config.yaml"
        if config_path.exists():
            config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            task_config = config.get("tasks", {}).get(task, {})
            model = task_config.get("model", "deepseek-pro")
            return model
    except Exception:
        pass

    # Fallback routing
    routing = {
        "volume_planner": "deepseek-pro",
        "state_machine_writer": "deepseek-pro",
        "sanitizer": "deepseek-pro",
        "originality_check": "deepseek-flash",
        "scene_router": "deepseek-flash",
        "negotiator": "deepseek-pro",
    }
    return routing.get(task, "deepseek-pro")


def _create_client_for_task(task: str, env=None):
    """为指定任务创建 LLM 客户端，自动选择模型和 provider。"""
    model_id = _route_model(task)
    try:
        from tools.studio.handlers import AVAILABLE_MODELS, _get_model_config
    except ImportError:
        AVAILABLE_MODELS = {
            "deepseek-pro": {"api_key_env": "LLM_API_KEY", "base_url_env": "LLM_BASE_URL", "model_name": "deepseek-chat"},
            "deepseek-flash": {"api_key_env": "LLM_API_KEY", "base_url_env": "LLM_BASE_URL", "model_name": "deepseek-chat"},
        }
        def _get_model_config(mid):
            return AVAILABLE_MODELS.get(mid, AVAILABLE_MODELS["deepseek-pro"])

    cfg = _get_model_config(model_id) if 'AVAILABLE_MODELS' in dir() else \
          AVAILABLE_MODELS.get(model_id, AVAILABLE_MODELS["deepseek-pro"])
    api_key = (env or os.environ).get(cfg.get("api_key_env", "LLM_API_KEY"), "").strip() or \
              (env or os.environ).get("LLM_API_KEY", "").strip()
    base_url = (env or os.environ).get(cfg.get("base_url_env", "LLM_BASE_URL"), "").strip() or \
               (env or os.environ).get("LLM_BASE_URL", "https://api.deepseek.com/v1").strip()

    if not api_key:
        return None
    try:
        import openai
        return openai.OpenAI(api_key=api_key, base_url=base_url)
    except ImportError:
        return None


# ═══════════════════════════════════════════════════════════
# 主流水线
# ═══════════════════════════════════════════════════════════

def execute_v6_pipeline(
    chapter_outline: str = "",
    chapter_num: int = 1,
    previous_summary: str = "",
    target_words: int = 3000,
    guidance: str = "",
    character_context: str = "",
    materials: list[dict] | None = None,
    needs_negotiation: bool = False,
    negotiation_chars: list[dict] | None = None,
) -> dict[str, Any]:
    """执行完整的 v6.0 工业化写作流水线。

    Args:
        chapter_outline: 章节大纲
        chapter_num: 章节号
        previous_summary: 前一章摘要
        target_words: 目标字数
        guidance: 写作指导
        character_context: 角色上下文
        materials: RAG 素材列表
        needs_negotiation: 是否需要谈判模拟
        negotiation_chars: 谈判角色列表

    Returns:
        {
            "chapter": 最终正文,
            "originality_score": 原创性评分,
            "sanitized": 是否已脱敏,
            "pipeline_steps": [...每步结果],
            "model_used": 使用的模型,
        }
    """
    steps = []
    workers = _create_client_for_task("state_machine_writer")

    # ── Step 1: 大纲细化 + 模型路由 ──
    route_model = _route_model("volume_planner")
    step1 = {
        "step": 1, "name": "大纲加载与模型路由",
        "model_routed": route_model,
        "chapter_num": chapter_num,
    }
    steps.append(step1)

    # ── Step 2: RAG 素材检索 ──
    rag_context = ""
    if materials:
        from tools.material_branch_rag import rag_inject_into_prompt
        rag_context = rag_inject_into_prompt(chapter_outline, materials, top_k=3)
        steps.append({
            "step": 2, "name": "RAG素材检索",
            "materials_count": len(materials),
            "injected": bool(rag_context),
        })

    # ── Step 3: 状态加载 ──
    context_parts = []
    if chapter_outline:
        context_parts.append(f"【本章大纲】\n{chapter_outline}")
    if previous_summary:
        context_parts.append(f"【前情摘要】\n{previous_summary}")
    if character_context:
        context_parts.append(f"【角色当前状态】\n{character_context}")
    if rag_context:
        context_parts.append(rag_context)
    if guidance:
        context_parts.append(f"【写作指导】\n{guidance}")
    full_context = "\n\n".join(context_parts)
    steps.append({"step": 3, "name": "状态加载", "context_chars": len(full_context)})

    # ── Step 4: 谈判预处理（可选） ──
    negotiation_dialogue = ""
    if needs_negotiation and negotiation_chars:
        from tools.multi_agent_negotiator import simulate_negotiation
        neg = simulate_negotiation(
            chapter_outline, negotiation_chars,
            _create_client_for_task("negotiator"),
        )
        negotiation_dialogue = neg.get("dialogue", "")
        if negotiation_dialogue and not negotiation_dialogue.startswith("【"):
            full_context += f"\n\n【谈判模拟对话】\n{negotiation_dialogue}"
        steps.append({
            "step": 4, "name": "谈判预处理",
            "used_llm": neg.get("used_llm", False),
            "dialogue_chars": len(negotiation_dialogue),
        })

    # ── Step 5: 正文生成 ──
    draft = _generate_chapter(full_context, target_words, workers)
    steps.append({"step": 5, "name": "正文生成", "draft_chars": len(draft)})

    if not draft.strip():
        return {"chapter": "", "error": "正文生成失败", "pipeline_steps": steps}

    # ── Step 6: 原创性自检 ──
    from tools.ai_traces_sanitizer import originality_check
    radar = originality_check(draft)
    steps.append({
        "step": 6, "name": "原创性雷达自检",
        "score": radar["originality_score"],
        "issues": radar["ai_traces_found"],
    })

    # 不达标则自动重写一次
    if radar["originality_score"] < 75 and workers:
        from tools.canvas_redrawer import redraw
        redrawn = redraw(draft, draft, "降低AI痕迹，增加人类手写感", workers)
        if redrawn.get("redrawn") and len(redrawn["redrawn"]) > 50:
            draft = redrawn["redrawn"]
            steps.append({
                "step": "6b", "name": "不及格自动重写",
                "method": redrawn.get("method"),
                "new_chars": len(draft),
            })
        # 重检
        radar = originality_check(draft)

    # ── Step 7: AI 痕迹脱敏 ──
    sanitizer = _create_client_for_task("sanitizer")
    if sanitizer:
        from tools.ai_traces_sanitizer import full_pipeline as sanitize_pipeline
        sanitized = sanitize_pipeline(draft, sanitizer)
        draft = sanitized.get("sanitized_text", draft)
        steps.append({
            "step": 7, "name": "AI痕迹脱敏",
            "final_score": sanitized.get("final_score", 0),
            "passed": sanitized.get("passed", False),
        })
    else:
        from tools.ai_traces_sanitizer import sanitize
        sanitized = sanitize(draft, "standard")
        draft = sanitized["text"]
        steps.append({
            "step": 7, "name": "AI痕迹脱敏(本地)",
            "changes": sanitized["changes"],
        })

    # ── Step 8: 状态更新（提取章节摘要） ──
    summary = _extract_summary(draft)
    steps.append({"step": 8, "name": "状态更新", "summary": summary})

    # 清除可能的 JSON/XML 标记
    draft = _clean_output(draft)

    return {
        "chapter": draft,
        "chapter_num": chapter_num,
        "target_words": target_words,
        "actual_words": len(draft.replace(" ", "").replace("\n", "")),
        "originality_score": radar.get("originality_score", 0),
        "summary": summary,
        "pipeline_steps": steps,
        "model_used": route_model,
    }


# ═══════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════

WRITER_PROMPT = """你是经验丰富的网文作者。请根据以下上下文写一章小说正文。

{context}

# 要求
- 字数：约{target_words}字
- 推动大纲节点，结尾卡在断章处
- 展示而非告知——用动作替代抽象心理描写
- 对话简洁有力，每人说话方式不同
- 感官细节不少于2处
- 严禁"倒吸一口凉气""虎躯一震""不由得""不禁""眼中闪过一丝"

仅输出正文，不要包含任何解释或JSON。"""


def _generate_chapter(context: str, target_words: int, client=None) -> str:
    """正文生成核心。"""
    if not client:
        return _fallback_chapter(context, target_words)

    prompt = WRITER_PROMPT.format(context=context[:12000], target_words=target_words)
    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=min(target_words * 3, 16000),
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        return _fallback_chapter(context, target_words, str(e))


def _fallback_chapter(context: str, target_words: int, error: str = "") -> str:
    """无 LLM 时的后备。"""
    note = f"💡 配置 LLM_API_KEY 获得 AI 写作能力" + (f"\n⚠ {error}" if error else "")
    return f"""{note}

# 第N章

（基于上下文的写作框架）

{context[:500]}

---

目标字数：{target_words} 字

下一步：
1. 配置 LLM_API_KEY 环境变量
2. 重新触发写作流水线
"""


def _extract_summary(text: str, max_len: int = 100) -> str:
    """从正文提取章节摘要。"""
    # 找第一段有意义的内容作为摘要
    paragraphs = [p.strip() for p in text.split("\n") if p.strip() and not p.startswith("#") and not p.startswith("💡")]
    for p in paragraphs:
        if len(p) > 20:
            return p[:max_len].replace("\n", " ")
    return text[:max_len].replace("\n", " ")


def _clean_output(text: str) -> str:
    """清除 LLM 输出中可能残留的 JSON/XML 标记。"""
    # 移除 state_update_json 块
    text = re.sub(r'<state_update_json>.*?</state_update_json>', '', text, flags=re.DOTALL)
    # 移除 Markdown 代码块标记
    text = re.sub(r'```\w*\n?', '', text)
    # 移除 JSON 块
    text = re.sub(r'\{[\s\S]*"chapter_number"[\s\S]*\}', '', text)
    return text.strip()


# ═══════════════════════════════════════════════════════════
# 简化入口（单步即可触发全流水线）
# ═══════════════════════════════════════════════════════════

def write_chapter_v6(
    premise: str = "",
    chapter_num: int = 1,
    previous: str = "",
    target_words: int = 3000,
    guidance: str = "",
) -> dict[str, Any]:
    """简化入口——一句话就能触发完整 v6.0 流水线。

    Args:
        premise: 本章梗概/大纲
        chapter_num: 章节号
        previous: 前一章摘要
        target_words: 目标字数
        guidance: 额外写作指导

    Returns:
        完整的流水线结果
    """
    return execute_v6_pipeline(
        chapter_outline=premise,
        chapter_num=chapter_num,
        previous_summary=previous,
        target_words=target_words,
        guidance=guidance,
    )
