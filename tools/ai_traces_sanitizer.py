"""燃灯 — AI 痕迹脱敏器 (四步精修法)

v6.0 规格书 Module 2.1：正文生成后深度脱敏，降低 AI 检测工具命中率。

四步流程:
    1. 结构变异 — 打破对称句长、随机短句、不均匀分段
    2. 词汇去模板 — humanization.yaml 规则 + 高频 AI 连接词替换
    3. 情感偏移 — 注入主观小情绪、感官细节
    4. 防查重改写 — 核心动词形容词同义替换
"""

from __future__ import annotations

import json
import os
import random
import re
from pathlib import Path
from typing import Any


# ═══════════════════════════════════════════════════════════
# 规则库
# ═══════════════════════════════════════════════════════════

AI_BANNED_PATTERNS = [
    # 高频连接词
    (r"然而", ["但是", "不过", "可", "却", "偏偏"]),
    (r"不禁", ["", "不自觉地", "下意识地"]),
    (r"不由得", ["", "忍不住", "不自觉"]),
    (r"缓缓", ["慢慢", "一点点", "逐渐", "慢悠悠地"]),
    (r"微微", ["轻轻", "浅浅", "稍稍"]),
    (r"心中暗想", ["心想", "琢磨着", "脑子里闪过"]),
    (r"眼中闪过一丝", ["眼神变了", "目光一凝", "眼里"]),
    (r"嘴角微微上扬", ["笑了笑", "咧嘴笑了", "嘴角一翘"]),
    (r"深吸一口气", ["吸了口气", "长出一口气", "重重吸了口气"]),
    (r"微微一笑", ["笑了笑", "咧嘴一笑", "扯了扯嘴角"]),
    (r"瞳孔一缩", ["眼神一紧", "眼皮跳了跳", "眼睛眯了起来"]),
    (r"脸色一变", ["脸色变了", "脸色沉了下来", "表情僵住"]),
    (r"倒吸一口凉气", ["吃了一惊", "愣住了", "脸色发白"]),
    (r"虎躯一震", ["身子一颤", "浑身一僵", "后背发凉"]),
    (r"沉声道", ["低声说", "压着嗓子", "声音低沉"]),
    (r"淡淡地说", ["说", "道", "不紧不慢地说"]),
    (r"冷冷地", ["冷声", "语气冰凉", "不带感情地"]),
    # AI 套话模式
    (r"由此可见", ["这么看来", "显然", "不用说"]),
    (r"综上所述", ["总之", "一句话", "说到底"]),
    (r"值得注意的是", ["关键是", "更要紧的是", ""]),
    (r"从某种意义上说", ["某种程度上", "某种意义上", ""]),
    (r"不可否认的是", ["确实", "说真的", "没错"]),
    (r"在这一刻", ["此刻", "这时候", "那一瞬间"]),
    (r"他意识到", ["他明白过来", "他忽然懂了", "他反应过来"]),
    (r"她感觉到", ["她觉得", "她察觉", "她隐约感到"]),
    # 生硬过渡
    (r"与此同时", ["同时", "另一边", "就在这时候"]),
    (r"另一方面", ["另一边", "再说", "另外"]),
    (r"首先.*?其次.*?最后", lambda m: _shuffle_sequence(m.group(0))),
]

# 感官词汇注入库
SENSORY_DETAILS = [
    # 听觉
    "指甲刮过墙壁的刺耳声", "远处隐约的狗吠", "风穿过窗缝的呜呜声",
    "水滴砸在石板上的啪嗒声", "骨节咔咔作响", "心跳声在耳膜里擂鼓",
    # 嗅觉
    "铁锈味混着潮湿的霉味", "烧焦的橡胶味", "栀子花甜腻的香气",
    "汗味混着廉价烟草的气息", "雨后泥土的腥味",
    # 触觉
    "指尖触到冰凉的金属", "粗粝的石墙硌着后背",
    "黏腻的冷汗贴着皮肤", "针扎般的刺痛从脊椎窜上来",
    # 视角内情绪
    "他妈的——脑子里只蹦出这两个字", "胃里翻了一下",
    "说不清是恼火还是好笑", "一阵没由来的烦躁",
    "心里咯噔一下", "嗓子眼发干",
]

# 中文同义词库（核心动词/形容词）
SYNONYM_MAP = {
    "看": ["望", "瞅", "瞥", "盯着", "扫了一眼", "目光落在"],
    "说": ["道", "开口", "出声", "冒出一句", "丢了一句"],
    "走": ["迈步", "抬脚", "踱", "穿过", "踏进"],
    "想": ["琢磨", "寻思", "盘算", "心里犯嘀咕", "脑子一转"],
    "愤怒": ["暴怒", "火冒三丈", "怒气上涌", "脸色铁青"],
    "害怕": ["发怵", "头皮发麻", "心里发毛", "后脊发凉"],
    "开心": ["咧嘴笑了", "心情大好", "心里舒坦", "眼中带笑"],
    "悲伤": ["心里堵得慌", "鼻子一酸", "眼眶发红", "心头沉甸甸的"],
    "惊讶": ["愣住", "吃了一惊", "瞪大眼", "脑子嗡了一下"],
    "美丽": ["惊艳", "好看得不像话", "耐看", "顺眼"],
    "强大": ["深不可测", "不好惹", "硬茬子", "实力摆在那"],
    "快速": ["眨眼间", "一溜烟", "蹭地一下", "闪电般"],
    "缓慢": ["不紧不慢", "慢悠悠", "磨磨蹭蹭", "一步一顿"],
}


# ═══════════════════════════════════════════════════════════
# 四步精修法
# ═══════════════════════════════════════════════════════════

def sanitize(text: str, intensity: str = "standard") -> dict[str, Any]:
    """AI 痕迹脱敏主入口。

    Args:
        text: 待处理的正文
        intensity: light(轻度)/standard(标准)/aggressive(激进)

    Returns:
        {"text": 脱敏后文本, "changes": 修改次数, "steps": 各步骤详情}
    """
    stats = {"original_len": len(text), "changes": 0, "steps": {}}

    # Step 1: 结构变异
    text, s1 = _step_structure_variation(text, intensity)
    stats["steps"]["structure"] = s1
    stats["changes"] += s1

    # Step 2: 词汇去模板
    text, s2 = _step_vocab_de_template(text, intensity)
    stats["steps"]["vocab"] = s2
    stats["changes"] += s2

    # Step 3: 情感偏移
    text, s3 = _step_emotion_offset(text, intensity)
    stats["steps"]["emotion"] = s3
    stats["changes"] += s3

    # Step 4: 防查重改写
    if intensity in ("standard", "aggressive"):
        text, s4 = _step_anti_plagiarism(text, intensity)
        stats["steps"]["anti_plagiarism"] = s4
        stats["changes"] += s4

    stats["final_len"] = len(text)
    return {"text": text, "changes": stats["changes"], "steps": stats["steps"]}


def _step_structure_variation(text: str, intensity: str) -> tuple[str, int]:
    """步骤1: 打破AI的均匀段落和对称句式。"""
    changes = 0
    paragraphs = text.split("\n\n")
    new_paragraphs = []

    for para in paragraphs:
        if not para.strip():
            new_paragraphs.append(para)
            continue

        sentences = re.split(r"(?<=[。！？…\.!?\n])", para)
        new_sentences = []

        for i, s in enumerate(sentences):
            s = s.strip()
            if not s:
                continue

            # 随机插入极短句（20%概率）
            if intensity in ("standard", "aggressive") and random.random() < 0.2 and len(s) > 15:
                short_phrases = ["他愣了。", "没由来的。", "啧。", "不对劲。", "等等。", "有意思。", "见鬼。", "完了。"]
                new_sentences.append(random.choice(short_phrases))
                changes += 1

            # 偶尔不加标点用空格（5%概率）
            if intensity == "aggressive" and random.random() < 0.05 and s.endswith("。"):
                s = s[:-1] + " "

            new_sentences.append(s)

        # 打破均匀分段：有的段落极短，有的极长
        merged = "".join(new_sentences)
        if intensity == "aggressive" and random.random() < 0.15:
            merged = merged.replace("\n", " ")  # 合并为单段

        new_paragraphs.append(merged)

    return "\n\n".join(new_paragraphs), changes


def _step_vocab_de_template(text: str, intensity: str) -> tuple[str, int]:
    """步骤2: 替换AI高频词汇和模板表达。"""
    changes = 0
    intensity_factor = {"light": 0.4, "standard": 0.7, "aggressive": 1.0}[intensity]

    for pattern, replacements in AI_BANNED_PATTERNS:
        if callable(replacements):
            # Lambda-based replacement
            matches = list(re.finditer(pattern, text))
            for m in reversed(matches):
                if random.random() < intensity_factor:
                    text = text[:m.start()] + replacements(m) + text[m.end():]
                    changes += 1
        elif random.random() < intensity_factor:
            new_count = len(re.findall(pattern, text))
            if new_count > 0:
                text = re.sub(pattern, lambda _: random.choice(replacements), text)
                changes += new_count

    return text, changes


def _step_emotion_offset(text: str, intensity: str) -> tuple[str, int]:
    """步骤3: 注入感官细节和主观情绪，替代空泛的心理描写。"""
    changes = 0
    intensity_factor = {"light": 0.15, "standard": 0.3, "aggressive": 0.45}[intensity]

    paragraphs = text.split("\n\n")
    new_paragraphs = []

    for para in paragraphs:
        if not para.strip() or len(para) < 60:
            new_paragraphs.append(para)
            continue

        # 在段落中随机位置注入感官细节
        if random.random() < intensity_factor:
            detail = random.choice(SENSORY_DETAILS)
            # 随机插入位置（段落中间偏后）
            insert_pos = len(para) * random.randint(4, 7) // 10
            # 找到最近的句号处插入
            dot_pos = para.rfind("。", 0, min(insert_pos + 20, len(para)))
            if dot_pos > 0:
                para = para[:dot_pos + 1] + detail + "。" + para[dot_pos + 1:]
            else:
                para = para + detail + "。"
            changes += 1

        new_paragraphs.append(para)

    return "\n\n".join(new_paragraphs), changes


def _step_anti_plagiarism(text: str, intensity: str) -> tuple[str, int]:
    """步骤4: 核心动词和形容词同义替换，降低查重率。"""
    changes = 0
    intensity_factor = {"standard": 0.3, "aggressive": 0.6}[intensity]

    for word, synonyms in SYNONYM_MAP.items():
        if random.random() < intensity_factor:
            pattern = re.compile(word)
            matches = list(pattern.finditer(text))
            for m in reversed(matches):
                if random.random() < 0.5:
                    replacement = random.choice(synonyms)
                    text = text[:m.start()] + replacement + text[m.end():]
                    changes += 1

    return text, changes


def _shuffle_sequence(match_text: str) -> str:
    """打乱'首先…其次…最后'的序列结构。"""
    return match_text.replace("首先", "头一条").replace("其次", "再者").replace("最后", "末了")


# ═══════════════════════════════════════════════════════════
# LLM 增强脱敏（可选的 AI 辅助）
# ═══════════════════════════════════════════════════════════

LLM_SANITIZER_PROMPT = """你是反AI检测专家与人类化精修大师。请将以下AI生成的小说初稿重写，保留原剧情与人物状态的同时，使其读起来像人类手写。

规则（四步精修法）：
1.【结构变异】打破对称句长。随机插入极短句（如"他愣了。""没由来的。"）。不均匀分段。
2.【词汇去模板】严禁"然而""不禁""不由得""缓缓""微微一笑""眼中闪过一丝""嘴角微扬""深吸一口气""由此可见""综上所述"。改成口语化表达。
3.【情感偏移】注入主观小情绪或内心吐槽。加入感官细节（闻到、听到、触到）。
4.【防查重改写】核心动词和形容词必须同义替换或意象转换。

原文：
{text}

仅输出人类化处理后的纯文本，不要包含任何解释。"""


def sanitize_with_llm(text: str, llm_client=None) -> dict[str, Any]:
    """使用 LLM 进行深度脱敏（可选增强）。"""
    # 先用规则引擎做基础脱敏
    result = sanitize(text, "standard")

    if llm_client:
        try:
            model = os.environ.get("LLM_MODEL", "deepseek-chat")
            resp = llm_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": LLM_SANITIZER_PROMPT.format(
                    text=result["text"])}],
                temperature=0.7,
                max_tokens=min(len(text) * 2, 16000),
            )
            llm_text = resp.choices[0].message.content or ""
            if llm_text and len(llm_text) > len(text) * 0.5:
                result["text"] = llm_text.strip()
                result["llm_enhanced"] = True
        except Exception:
            pass

    return result


# ═══════════════════════════════════════════════════════════
# 原创性雷达评分
# ═══════════════════════════════════════════════════════════

def originality_check(text: str) -> dict[str, Any]:
    """快速原创性检测（规则引擎，零成本）。"""
    issues = []
    score = 100

    # 检查AI高频词
    for pattern, _ in AI_BANNED_PATTERNS:
        if callable(_):
            continue
        matches = re.findall(pattern, text)
        if matches:
            penalty = min(len(matches) * 3, 30)
            score -= penalty
            issues.append({"pattern": pattern, "count": len(matches), "penalty": penalty})

    # 检查句式重复（连续相同长度句子）
    sentences = [s.strip() for s in re.split(r"[。！？]", text) if s.strip()]
    if len(sentences) > 10:
        lengths = [len(s) for s in sentences]
        # 检查是否有连续4句长度差异<3个字符
        for i in range(len(lengths) - 3):
            if max(lengths[i:i+4]) - min(lengths[i:i+4]) < 5:
                score -= 5
                issues.append({"pattern": "句式重复(均匀句长)", "count": 1, "penalty": 5})
                break

    # 检查段落均匀性
    paragraphs = text.split("\n\n")
    if len(paragraphs) > 5:
        para_lens = [len(p) for p in paragraphs if p.strip()]
        if para_lens and max(para_lens) / max(min(para_lens), 1) < 2.5:
            score -= 8
            issues.append({"pattern": "段落长度过于均匀", "count": 1, "penalty": 8})

    score = max(0, min(100, score))
    return {
        "originality_score": score,
        "ai_traces_found": [i["pattern"] for i in issues],
        "need_rewrite": score < 75,
        "issues": issues,
        "verdict": _get_verdict(score),
    }


def _get_verdict(score: int) -> str:
    if score >= 90:
        return "优秀 — 人类手写感强，AI 检测大概率通过"
    elif score >= 75:
        return "良好 — 建议过一遍脱敏器优化"
    elif score >= 60:
        return "一般 — 有明显 AI 痕迹，建议脱敏处理后重审"
    else:
        return "需重写 — AI 痕迹严重，必须深度脱敏"


# ═══════════════════════════════════════════════════════════
# 完整流水线: 原创性检测 → 脱敏 → 复检
# ═══════════════════════════════════════════════════════════

def full_pipeline(text: str, llm_client=None, target_score: int = 80) -> dict[str, Any]:
    """完整流水线：检测 → 脱敏 → 复检。

    模拟 v6.0 规格书的第6-7步。
    """
    result = {
        "original_text": text[:200] + "…" if len(text) > 200 else text,
        "original_score": 0,
        "sanitized_text": "",
        "final_score": 0,
        "passed": False,
    }

    # 第6步：原创性检测
    radar = originality_check(text)
    result["original_score"] = radar["originality_score"]
    result["original_issues"] = radar["ai_traces_found"]

    if radar["originality_score"] >= target_score:
        result["sanitized_text"] = text
        result["final_score"] = radar["originality_score"]
        result["passed"] = True
        result["note"] = f"无需脱敏，原始评分{radar['originality_score']}已达标"
        return result

    # 第7步：脱敏处理
    sanitized = sanitize_with_llm(text, llm_client)
    result["sanitized_text"] = sanitized["text"]
    result["sanitize_changes"] = sanitized["changes"]

    # 复检
    recheck = originality_check(sanitized["text"])
    result["final_score"] = recheck["originality_score"]
    result["passed"] = recheck["originality_score"] >= target_score
    result["final_issues"] = recheck["ai_traces_found"]

    if not result["passed"]:
        result["note"] = f"脱敏后评分{recheck['originality_score']}仍低于{target_score}，建议人工复核或提高脱敏强度"

    return result
