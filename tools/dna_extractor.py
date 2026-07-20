"""燃灯 DNA 提取器 — 作品风格指纹系统

基于「分段阅读 → 硬数据锚定 → LLM 深度分析 → 加权融合」架构。
提取 16 层作品 DNA，支持多本融合创作。

灵感来源: works-dna-extractor / Echo-Quill Alchemist / novel-writer-style-cn
"""

from __future__ import annotations

import json
import re
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


# ═══════════════════════════════════════════════════════════
# 16 层 DNA 定义
# ═══════════════════════════════════════════════════════════

DNA_LAYERS = {
    "layer_01_sentence": "句法指纹 — 平均句长、句长分布、短句/长句比例",
    "layer_02_vocabulary": "词汇指纹 — 高频词、独有词、词性分布",
    "layer_03_punctuation": "标点指纹 — 逗号/句号/感叹号/省略号密度",
    "layer_04_paragraph": "段落指纹 — 平均段长、段间距、场景切换频率",
    "layer_05_dialogue": "对话指纹 — 对话占比、引导词偏好、对白节奏",
    "layer_06_description": "描写指纹 — 环境/外貌/心理描写比例",
    "layer_07_narrative_voice": "叙述口吻 — 第一/三人称、叙述距离、态度倾向",
    "layer_08_rhythm": "节奏指纹 — 章长分布、高潮间隔、喘息章模式",
    "layer_09_character_philosophy": "人物哲学 — 主角类型、反派深度、配角独立性",
    "layer_10_emotion_palette": "情感光谱 — 主情绪、情绪变奏、悲剧/喜剧倾向",
    "layer_11_hook_pattern": "钩子模式 — 开篇钩子、章末悬念、反转密度",
    "layer_12_worldview": "世界观指纹 — 魔法体系硬度、历史深度、社会复杂度",
    "layer_13_plot_structure": "情节结构 — 主线/支线比例、高潮布局、伏笔回收率",
    "layer_14_cognitive_frame": "认知框架 — 作者核心假设、隐含价值观、禁忌区域",
    "layer_15_language_texture": "语言质感 — 用词精确度、修辞密度、通感使用",
    "layer_16_reader_contract": "读者契约 — 开篇承诺、爽点密度、读者期待管理",
}


@dataclass
class HardStats:
    """硬数据统计 — 确定性分析，作为 LLM 锚点"""
    total_chars: int = 0
    total_words: int = 0
    total_sentences: int = 0
    total_paragraphs: int = 0
    avg_sentence_len: float = 0
    sentence_len_distribution: dict[str, int] = field(default_factory=dict)
    top_words: list[tuple[str, int]] = field(default_factory=list)
    punctuation_density: dict[str, float] = field(default_factory=dict)
    dialogue_ratio: float = 0
    paragraph_avg_len: float = 0
    chapter_break_count: int = 0


def compute_hard_stats(text: str) -> dict[str, Any]:
    """计算硬数据 — 客观统计，不做任何推测"""
    chars = len(text)

    # 分句
    sentences = _split_sentences(text)
    total_sentences = len(sentences)

    # 分词 (中文粗分: 以标点/空格为界)
    words_raw = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
    total_words = len(words_raw)

    # 句长
    sent_lens = [len(re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]', s)) for s in sentences if s.strip()]
    avg_sent = round(sum(sent_lens) / max(1, len(sent_lens)), 1) if sent_lens else 0

    # 句长分布
    short = sum(1 for l in sent_lens if l < 10)
    mid = sum(1 for l in sent_lens if 10 <= l <= 30)
    long = sum(1 for l in sent_lens if l > 30)
    dist = {"短句(<10字)": short, "中句(10-30字)": mid, "长句(>30字)": long}

    # 词频 Top 20 (过滤停用词)
    stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
                 "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
                 "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些"}
    word_counts = Counter(w for w in words_raw if len(w) > 1 and w not in stopwords)
    top_words = word_counts.most_common(20)

    # 标点密度 (每千字)
    punct = {
        "逗号": text.count("，") / max(1, chars / 1000),
        "句号": text.count("。") / max(1, chars / 1000),
        "感叹号": text.count("！") / max(1, chars / 1000),
        "问号": text.count("？") / max(1, chars / 1000),
        "省略号": (text.count("…") + text.count("...")) / max(1, chars / 1000),
    }
    punct_d = {k: round(v, 1) for k, v in punct.items()}

    # 对话比例 (引号内容)
    dialogue_chars = sum(len(m) for m in re.findall(r'"[^"]*"|"[^"]*"|'[^']*'|'[^']*'', text))
    dialogue_ratio = round(dialogue_chars / max(1, chars) * 100, 1)

    # 段落
    paras = [p for p in text.split("\n") if p.strip()]
    total_paras = len(paras)
    avg_para = round(sum(len(p) for p in paras) / max(1, total_paras), 1)

    # 章节数
    chapter_count = len(re.findall(r'^第[一二三四五六七八九十百千\d]+[章回节]', text, re.MULTILINE))

    return {
        "total_chars": chars,
        "total_words": total_words,
        "total_sentences": total_sentences,
        "total_paragraphs": total_paras,
        "avg_sentence_len": avg_sent,
        "sentence_length_distribution": dist,
        "top_words": [{"word": w, "count": c} for w, c in top_words[:15]],
        "punctuation_per_1k_chars": punct_d,
        "dialogue_ratio_percent": dialogue_ratio,
        "avg_paragraph_len": avg_para,
        "chapter_count": chapter_count,
    }


def _split_sentences(text: str) -> list[str]:
    """中文分句"""
    result = []
    buf = ""
    for ch in text:
        buf += ch
        if ch in "。！？!?…\n":
            if buf.strip():
                result.append(buf.strip())
            buf = ""
    if buf.strip():
        result.append(buf.strip())
    return result


# ═══════════════════════════════════════════════════════════
# DNA 提取
# ═══════════════════════════════════════════════════════════

def extract_dna(text: str, title: str = "", llm_client=None) -> dict[str, Any]:
    """提取作品 DNA — 硬数据 + LLM 深度分析"""
    hard = compute_hard_stats(text)

    dna = {
        "meta": {
            "title": title or "未命名",
            "chars": hard["total_chars"],
            "words": hard["total_words"],
            "extracted_at": __import__("time").strftime("%Y-%m-%d %H:%M"),
        },
        "hard_stats": hard,
        "layers": {},
    }

    # 从硬数据推断的基础层
    _infer_basic_layers(dna, hard, text)

    # LLM 深度层 (如有)
    if llm_client:
        try:
            _llm_deep_analysis(dna, text, hard, llm_client)
            dna["llm_analyzed"] = True
        except Exception as e:
            dna["llm_error"] = str(e)[:100]
            dna["llm_analyzed"] = False
    else:
        dna["llm_analyzed"] = False
        dna["layers"]["llm_note"] = "未提供 LLM 客户端，仅完成硬数据层分析"

    return dna


def _infer_basic_layers(dna: dict, hard: dict, text: str) -> None:
    """从硬数据推断基础 DNA 层"""
    layers = dna["layers"]

    # Layer 1: 句法
    dist = hard["sentence_length_distribution"]
    short_pct = dist.get("短句(<10字)", 0)
    long_pct = dist.get("长句(>30字)", 0)
    total_s = max(1, sum(dist.values()))
    if short_pct / total_s > 0.5:
        layers["layer_01_sentence"] = "短句驱动型 — 快节奏，适合爽文/都市/悬疑"
    elif long_pct / total_s > 0.4:
        layers["layer_01_sentence"] = "长句叙事型 — 慢节奏，适合文学性/世界构建类"
    else:
        layers["layer_01_sentence"] = "混合型 — 句长变化丰富，节奏张弛有度"

    # Layer 2: 词汇
    top = hard["top_words"][:5]
    layers["layer_02_vocabulary"] = f"高频词: {', '.join(w['word'] for w in top)}" if top else "词频分布均匀"

    # Layer 3: 标点
    punct = hard["punctuation_per_1k_chars"]
    if punct.get("感叹号", 0) > 10:
        layers["layer_03_punctuation"] = "高情绪密度 — 大量感叹号，偏热血/激烈"
    elif punct.get("问号", 0) > 5:
        layers["layer_03_punctuation"] = "疑问驱动 — 常用问号设悬，偏悬疑/推理"
    else:
        layers["layer_03_punctuation"] = "平实 — 标点使用克制，偏严肃/文学类"

    # Layer 5: 对话
    dr = hard["dialogue_ratio_percent"]
    if dr > 30:
        layers["layer_05_dialogue"] = f"对话密集型 ({dr}%) — 以人物互动推动剧情"
    elif dr > 15:
        layers["layer_05_dialogue"] = f"均衡型 ({dr}%) — 对话与叙述兼顾"
    else:
        layers["layer_05_dialogue"] = f"叙述主导型 ({dr}%) — 以作者叙述推进故事"

    # Layer 7: 叙述口吻
    if "我" in text[:200] and "他" not in text[:200]:
        layers["layer_07_narrative_voice"] = "第一人称 — 贴近主角内心"
    elif re.search(r"他|她", text[:100]):
        layers["layer_07_narrative_voice"] = "第三人称 — 客观/半全知视角"

    # Layer 8: 节奏
    sent_count = hard.get("total_sentences", 0)
    chapter_count = hard.get("chapter_count", 0)
    if chapter_count > 0:
        avg_per_chapter = sent_count / chapter_count
        if avg_per_chapter < 50:
            layers["layer_08_rhythm"] = "快节奏短章节 — 适合移动端碎片阅读"
        elif avg_per_chapter > 200:
            layers["layer_08_rhythm"] = "长章节史诗节奏 — 适合沉浸式深度阅读"
        else:
            layers["layer_08_rhythm"] = "中等节奏 — 章节长度稳定"

    # Layer 11: 钩子
    hooks = 0
    if re.search(r"突然|忽然|竟然|没想到|难道|原来", text[:1000]):
        hooks += 1
    if re.search(r"[？！].{0,10}$", text.split("。")[-1] if text.split("。") else ""):
        hooks += 1
    layers["layer_11_hook_pattern"] = f"{'强' if hooks >= 2 else '弱'}钩子型 — 开篇{'有' if hooks else '缺'}悬念"


def _llm_deep_analysis(dna: dict, text: str, hard: dict, llm_client) -> None:
    """LLM 深度分析高层 DNA（叙事哲学/情感算法/认知框架）"""
    import os

    sample = text[:5000]
    stats = json.dumps({
        "avg_sentence_len": hard["avg_sentence_len"],
        "dialogue_ratio": hard["dialogue_ratio_percent"],
        "top_words": [w["word"] for w in hard["top_words"][:8]],
        "chapter_count": hard["chapter_count"],
    }, ensure_ascii=False)

    prompt = f"""你是文学分析专家。请基于以下数据对这本小说进行深度分析:

【硬数据统计】
{stats}

【前5000字样本】
{sample[:3000]}

请用 JSON 格式返回:
{{
  "narrative_strategy": "叙事策略(30字内)",
  "dialogue_style": "对话风格特征(30字内)",
  "emotional_algorithm": "情感操控手法(30字内)",
  "core_hypothesis": "作者的核心假设/隐含价值观(50字内)",
  "forbidden_zones": "作者绝不触碰的区域(30字内)",
  "reader_promise": "给读者的核心承诺是什么(30字内)",
  "style_signature": "一句话风格签名(40字内)"
}}"""

    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        response = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600,
        )
        content = response.choices[0].message.content or "{}"
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            llm_result = json.loads(json_match.group())
            dna["layers"]["layer_10_emotion_palette"] = llm_result.get("emotional_algorithm", "")
            dna["layers"]["layer_13_plot_structure"] = llm_result.get("narrative_strategy", "")
            dna["layers"]["layer_14_cognitive_frame"] = llm_result.get("core_hypothesis", "")
            dna["layers"]["layer_16_reader_contract"] = llm_result.get("reader_promise", "")
            dna["layers"]["layer_15_language_texture"] = llm_result.get("style_signature", "")
            dna["layers"]["layer_05_dialogue_ai"] = llm_result.get("dialogue_style", "")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
# 风格融合（加权）
# ═══════════════════════════════════════════════════════════

def blend_styles(dnas: list[dict], weights: list[float] | None = None,
                 blend_instruction: str = "", llm_client=None) -> dict[str, Any]:
    """加权风格融合

    Args:
        dnas: 多本书的 DNA 提取结果
        weights: 权重列表 (如 [0.6, 0.4])，不传则均分
        blend_instruction: 融合方向指引
        llm_client: LLM 客户端
    """
    if len(dnas) < 2:
        return {"error": "至少需要 2 本书的 DNA 才能融合"}

    if not weights:
        weights = [1.0 / len(dnas)] * len(dnas)
    weights = [w / sum(weights) for w in weights]  # 归一化

    blend = {
        "books": [d["meta"]["title"] for d in dnas],
        "weights": [round(w, 3) for w in weights],
        "instruction": blend_instruction or "均衡融合各书风格",
        "hard_fusion": {},
        "layer_fusion": {},
    }

    # 硬数据融合 (加权平均)
    hard_keys = ["avg_sentence_len", "dialogue_ratio_percent", "avg_paragraph_len"]
    for key in hard_keys:
        vals = []
        for d, w in zip(dnas, weights):
            val = d.get("hard_stats", {}).get(key, 0)
            if isinstance(val, (int, float)):
                vals.append(val * w)
        if vals:
            blend["hard_fusion"][key] = round(sum(vals), 1)

    # DNA 层融合 — 找出共性和差异
    all_layers = set()
    for d in dnas:
        all_layers.update(k for k in d.get("layers", {}).keys() if not k.startswith("llm_"))

    for layer in sorted(all_layers):
        values = []
        for d, w in zip(dnas, weights):
            val = d.get("layers", {}).get(layer, "")
            if val:
                values.append(val)
        if len(values) >= 2:
            # 找共性
            common = [v for v in values if sum(1 for v2 in values if v2 == v) >= 2]
            blend["layer_fusion"][layer] = {
                "common": common[0] if common else "风格各异",
                "individual": values,
                "dominant_book": dnas[weights.index(max(weights))]["meta"]["title"],
            }

    # LLM 融合建议
    if llm_client:
        try:
            _llm_blend_advice(blend, dnas, weights, llm_client)
            blend["llm_advice"] = True
        except Exception:
            blend["llm_advice"] = False

    # 生成融合后的风格描述
    blend["blended_style_summary"] = _generate_blend_summary(blend)
    return blend


def _llm_blend_advice(blend: dict, dnas: list[dict], weights: list[float], client) -> None:
    """LLM 生成融合建议"""
    import os
    book_summaries = []
    for d, w in zip(dnas, weights):
        layers = {k: v for k, v in d.get("layers", {}).items() if k.startswith("layer_")}
        book_summaries.append(f"{d['meta']['title']} (权重{w:.0%}): {json.dumps(layers, ensure_ascii=False)[:300]}")

    prompt = f"""你是文学风格融合专家。请基于以下书目的 DNA 分析，给出风格融合建议:

{chr(10).join(book_summaries)}

融合方向: {blend.get('instruction', '均衡融合')}

用 JSON 返回:
{{
  "fusion_name": "融合风格命名(10字内)",
  "writing_advice": "具体写作建议(80字内)",
  "target_reader": "目标读者群体(20字内)",
  "risk": "潜在风险(30字内)"
}}"""

    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=400,
        )
        content = response.choices[0].message.content or "{}"
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            blend["llm_advice_result"] = json.loads(json_match.group())
    except Exception:
        pass


def _generate_blend_summary(blend: dict) -> str:
    """生成人类可读的融合摘要"""
    lines = [f"📚 融合 {len(blend['books'])} 本书", ""]
    for b, w in zip(blend["books"], blend["weights"]):
        lines.append(f"  {b}: {w:.0%}")

    lines.append(f"\n🎯 融合方向: {blend['instruction']}")

    hf = blend.get("hard_fusion", {})
    if hf.get("avg_sentence_len"):
        lines.append(f"\n📏 融合后平均句长: {hf['avg_sentence_len']} 字")
    if hf.get("dialogue_ratio_percent"):
        lines.append(f"💬 对话占比: {hf['dialogue_ratio_percent']}%")

    lf = blend.get("layer_fusion", {})
    if lf:
        lines.append("\n🎨 关键风格融合:")
        for layer, info in list(lf.items())[:5]:
            label = DNA_LAYERS.get(layer, layer)
            lines.append(f"  {label}: {info.get('common', '融合')[:50]}")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════

def extract_and_save_dna(text: str, title: str, output_dir: str = "", llm_client=None) -> dict:
    """提取 DNA 并保存为文件"""
    from pathlib import Path
    import yaml

    dna = extract_dna(text, title, llm_client)
    out_path = Path(output_dir) / f"{title}_dna.yaml" if output_dir else Path(f"{title}_dna.yaml")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.dump(dna, allow_unicode=True, default_flow_style=False), encoding="utf-8")

    return {
        "ok": True,
        "dna": dna,
        "saved_to": str(out_path),
    }
