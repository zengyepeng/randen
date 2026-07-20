"""燃灯创作引擎 — 从零到一的四步创作启动

提供：
1. 扫榜分析：根据目标平台分析市场风向，推荐蓝海赛道
2. 拆书分析：将参考作品拆解为爽点/金手指/钩子结构
3. 脑洞完善：将一句话灵感扩展为核心设定体系
4. 开篇诊断：分析/优化第一章的开篇钩子和节奏

所有分析均为本地结构化处理 + 可选 AI 增强。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── 数据模型 ──────────────────────────────────────────────

@dataclass
class MarketInsight:
    """赛道分析结果"""
    genre: str
    traffic: str  # 高/中/低
    competition: str  # 激烈/正常/蓝海
    newcomer_friendly: str  # 友好/一般/不推荐
    tip: str


@dataclass
class BookDissection:
    """拆书分析结果"""
    title: str
    golden_finger: str = ""
    hook_pattern: str = ""
    rhythm: str = ""
    character_arc: str = ""
    success_factors: list[str] = field(default_factory=list)
    chapter_breakdown: list[dict[str, str]] = field(default_factory=list)


@dataclass
class CoreSetting:
    """核心设定"""
    title_hook: str = ""  # 书名钩子
    premise: str = ""  # 一句话梗概
    golden_finger: str = ""  # 金手指
    golden_finger_cost: str = ""  # 金手指代价
    unique_selling_point: str = ""  # 独特卖点
    target_emotion: str = ""  # 目标情绪
    protagonist_flaw: str = ""  # 主角缺陷
    world_rules: str = ""  # 世界规则亮点
    chapter_zero_hook: str = ""  # 第一章钩子


# ── 预设知识库 ─────────────────────────────────────────────

# 网文平台分析（无需联网，基于公开信息）
PLATFORM_INSIGHTS: dict[str, list[MarketInsight]] = {
    "番茄小说": [
        MarketInsight("都市系统流", "高", "正常", "友好",
                      "每天超5万人在搜索含'系统'关键词，但精品供给不足。建议切入'社畜金手指'子赛道。"),
        MarketInsight("末世生存", "中高", "正常", "友好",
                      "2026上半年末世文阅读量增长42%，但开篇同质化严重。差异化点：非打怪升级的生存路线。"),
        MarketInsight("快穿攻略", "高", "激烈", "一般",
                      "头部作品垄断流量，新人需找细分切入点如'综艺快穿''科举快穿'。"),
        MarketInsight("规则怪谈", "中高", "蓝海", "友好",
                      "2025年兴起的小众赛道，读者增长快，优秀作品少。要点：规则设计要有趣而非恐怖。"),
        MarketInsight("脑洞反套路", "中高", "蓝海", "友好",
                      "读者看腻了传统套路，反套路文近年追读率显著高于同类。核心是在预期处反转。"),
    ],
    "起点中文网": [
        MarketInsight("凡人修仙流", "高", "激烈", "不推荐",
                      "头部大神垄断，新人难突围。可考虑'穿越+修仙'混搭切口。"),
        MarketInsight("科幻星际", "中", "正常", "友好",
                      "硬科幻门槛高但软科幻+网文节奏有空间。推荐：星际种田、星际直播流。"),
        MarketInsight("都市异能", "高", "正常", "友好",
                      "受众广但需差异化。热点：体制内异能、快递小哥觉醒。"),
    ],
    "知乎盐言": [
        MarketInsight("短篇虐文", "高", "激烈", "一般",
                      "短篇核心是开篇钩子+情绪反转，1万字内完成起承转合。"),
        MarketInsight("悬疑短篇", "中", "正常", "友好",
                      "2-3万字最佳，开头设谜结尾反转。盐言短篇对逻辑要求低于长篇。"),
    ],
    "默认": [
        MarketInsight("都市系统流", "高", "正常", "友好",
                      "系统流是最容易入门的新人赛道。金手指明确、升级清晰、爽点密集。"),
        MarketInsight("规则怪谈", "中高", "蓝海", "友好",
                      "2025年兴起的新赛道，供给不足。要点：规则设计有趣而非恐怖。"),
        MarketInsight("脑洞反套路", "中高", "蓝海", "友好",
                      "预期反转是当前网文最大的流量密码。核心在读者以为会这样，但发生了那样。"),
        MarketInsight("种田流/基建流", "中", "蓝海", "友好",
                      "慢节奏但粘性高。适合不追求爆款、想稳定积累读者群的新人。"),
        MarketInsight("穿越+职场", "中", "正常", "友好",
                      "避开纯玄幻红海，用现代职场逻辑穿越古代/异世。卖点：降维打击。"),
    ],
}

# 网文题材基础引导
GENRE_GUIDES = {
    "系统流": {
        "key_question": "你给主角一个什么系统？它有什么独特的限制？",
        "golden_finger_examples": [
            "签到系统（每日打卡获得奖励，但签到地点越来越危险）",
            "反套路系统（发布和常规预期相反的任务，做越离谱的事奖励越高）",
            "吐槽系统（吐槽别人的行为能获得属性点，但得罪人）",
        ],
        "pitfalls": [
            "❌ 系统包揽一切 → 读者没有期待感",
            "❌ 数值暴涨没有代价 → 爽不过10章就腻",
            "✅ 系统有明确的功能范围 + 使用限制 + 代价",
        ],
    },
    "重生穿越": {
        "key_question": "主角重生/穿越的契机是什么？这一世要改变的核心事件是什么？",
        "golden_finger_examples": [
            "先知记忆（知道未来走向，但蝴蝶效应让熟悉的历史逐渐偏离）",
            "前世的技能/知识（程序员穿越修真界、医生穿越古代、电商运营穿越异世）",
            "系统辅助（签到系统、任务系统配合重生信息差）",
        ],
        "pitfalls": [
            "❌ 重生后一帆风顺 → 读者没有紧张感",
            "❌ 完全按前世轨迹走 → 少了惊喜",
            "✅ 预设'蝴蝶效应'——主角的每个改变都带来意想不到的连锁反应",
            "✅ 设一个'必须阻止'的事件作为主线锚点",
        ],
    },
    "都市系统流": {
        "key_question": "系统在城市背景下能做什么别人做不了的事？",
        "golden_finger_examples": [
            "每日签到系统（社畜逆袭、学生翻身）",
            "技能面板系统（从打工人到全能大神）",
            "反套路系统（在预期处反转的都市爽文）",
        ],
        "pitfalls": [
            "❌ 系统太万能 → 失去真实感",
            "❌ 只写打脸爽不加人物成长 → 30章后疲劳",
            "✅ 系统有明确的成长曲线和阶段限制",
        ],
    },
    "种田流/基建流": {
        "key_question": "主角要建造什么？这个建造过程的独特乐趣是什么？",
        "golden_finger_examples": [
            "农业系统（改良种子、加速生长、增产增收）",
            "建造系统（从茅草屋到城池，步步升级）",
            "经营系统（经营店铺、领地、国家，数据化爽感）",
        ],
        "pitfalls": [
            "❌ 只写种田没有冲突 → 读者无聊",
            "❌ 建造过程没有阻力 → 缺少成就感",
            "✅ 每阶段设定一个外部威胁或资源瓶颈",
            "✅ 展示建造成果的视觉化对比（前后变化）",
        ],
    },
    "女频甜宠": {
        "key_question": "男女主的关系发展有什么独特的看点？HE是必然的，但'怎么走到HE'才是卖点。",
        "golden_finger_examples": [
            "情感系统（能看到好感度数值，但数值有时不准导致误会）",
            "重生先知（知道谁是渣男/真爱，但蝴蝶效应让感情线偏移）",
            "替身觉醒（穿成虐文女主，拒绝走原著路线）",
        ],
        "pitfalls": [
            "❌ 男主太完美无缺点 → 像纸片人",
            "❌ 感情进展太快没有阻力 → 读者不着急",
            "✅ 男主要有至少一个让读者想骂他的缺点",
            "✅ 甜宠不等于没有冲突——误会、身份差距、外部阻力",
        ],
    },
    "玄幻修仙": {
        "key_question": "主角的修炼体系有什么独特之处？为什么别人做不到？",
        "golden_finger_examples": [
            "废柴体质觉醒（看似最差的资质，其实是万古第一奇才）",
            "随身老爷爷（戒指里的强者指导，但要付出代价）",
            "吞噬系统（猎杀获取能力，但数量有限且越来越难）",
            "签到诸天（每天在不同地点签到获得功法/丹药）",
        ],
        "pitfalls": [
            "❌ 升级太快没有瓶颈 → 30万字后无内容可写",
            "❌ 每个境界都一个套路 → 换地图换皮不换骨",
            "✅ 每跨越一个大境界伴随世界观扩张",
            "✅ 用'资源稀缺'制造冲突——所有人都想要主角手中的东西",
        ],
    },
    "悬疑推理": {
        "key_question": "核心谜题是什么？读者能在第几章猜到真相？",
        "golden_finger_examples": [
            "记忆回溯（能短暂回到案发现场，但每次使用折寿）",
            "灵异直觉（能感知到谎言，但分不清是自己多疑还是真的）",
            "系统推演（犯罪心理画像系统，但信息越少越不准）",
        ],
        "pitfalls": [
            "❌ 谜底太早暴露 → 读者没了追读动力",
            "❌ 谜底太晚揭示 → 读者忘了前面的线索",
            "✅ 每3-5章释放一个小线索，每10章给一个假答案再推翻",
            "✅ 让读者觉得'我差一点就猜到了'——是最佳体验",
        ],
    },
    "规则怪谈": {
        "key_question": "核心规则是什么？违反规则的后果是什么？",
        "golden_finger_examples": [
            "主角能看见别人看不见的规则提示",
            "主角自带一条'免疫一次规则惩罚'的被动",
            "主角能从规则漏洞中找到奖励",
        ],
        "pitfalls": [
            "❌ 规则太复杂 → 读者看不懂",
            "❌ 只靠恐怖吓人 → 网文读者要的是解谜的爽感",
            "✅ 3-5条核心规则，逐步揭示，每次违反都有直观后果",
        ],
    },
    "脑洞反套路": {
        "key_question": "读者预期什么？你在哪里反转？",
        "golden_finger_examples": [
            "迪化：周围人脑补主角是世外高人（主角其实很菜）",
            "反向金手指：系统给的能力都不是用来战斗的（但总能歪打正着）",
            "平行思维：主角的思考方式和世界观里的所有人都不一样",
        ],
        "pitfalls": [
            "❌ 为了反转而反转 → 逻辑崩坏",
            "❌ 读者get不到笑点 → 需要铺垫预期再打破",
            "✅ 先让读者形成预期（2-3章），然后精准打破一个预期",
        ],
    },
}

# 开篇诊断清单
OPENING_CHECKLIST = [
    ("hook", "第一句话能不能勾住读者？",
     "读者打开了你的书，第一句话看完——他有没有产生'然后呢？'的冲动？如果没有，试试用对话或反常事件开头。"),
    ("conflict", "章末有没有让人抓心挠肝的悬念？",
     "读者翻到章末最后一句话——他是不是立刻想点下一章？如果不是，加一个小反转、一个未解答的问题、或者一个突发危机。"),
    ("exposition", "开篇有没有大段'说明书'？",
     "你前300字是不是在介绍'这个世界分为三大洲五大势力……'？读者不想看说明书，他们想感受。把设定藏进角色的动作和对话里。"),
    ("character_goal", "主角到底想要什么？",
     "读者看完前500字，能不能说清楚'这个主角想要什么'？如果不能，让主角在开头就表现出一个具体的、有障碍的愿望。"),
    ("emotion", "开篇有没有让人有感觉？",
     "你的第一章让读者感觉到了什么？好奇？紧张？心疼？愤怒？如果什么感觉都没有，那就只是在读流水账。选一个情绪，在开头就砸给读者。"),
    ("rhythm", "节奏有没有变化？",
     "从头到尾一个速度=无聊。试试：紧张的场景写短句（10字以内），舒缓的场景写长句——读者的大脑需要节奏来保持注意力。"),
    ("showing", "有没有让读者'看见'而不是'被告知'？",
     "不要说'他很愤怒'，写他'一拳砸碎了桌上的杯子'。不要告诉读者世界规则，让他们从角色的遭遇里自己悟出来。"),
]


# ── 核心功能 ───────────────────────────────────────────────

def analyze_market(platform: str = "默认") -> list[dict[str, str]]:
    """扫榜分析：基于平台返回推荐赛道"""
    insights = PLATFORM_INSIGHTS.get(platform, PLATFORM_INSIGHTS["默认"])
    return [
        {
            "genre": i.genre,
            "traffic": i.traffic,
            "competition": i.competition,
            "newcomer": i.newcomer_friendly,
            "tip": i.tip,
        }
        for i in insights
    ]


def dissect_book(text: str, title: str = "未命名作品") -> dict[str, Any]:
    """拆书分析：从正文中提取结构特征"""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return {"error": "正文为空，请提供至少一段文字进行拆解"}

    # 基础结构分析
    chapter_count = max(1, len(paragraphs) // 40)  # 估算章节数
    hooks_found: list[str] = []
    golden_finger_candidates: list[str] = []

    # 搜索钩子模式
    hook_patterns = [
        (r"(突然|忽然|就在这时|没想到|万万没想到|却|竟然|居然)", "转折型钩子"),
        (r"(\?|！.*$)", "悬念型钩子"),
        (r"(如果|假如|要是).*(就好了|该多好|的话)", "假设型钩子"),
        (r"(他|她|它)(慢慢|缓缓|悄悄|偷偷)", "动作悬念型"),
        (r"系统|面板|任务|奖励|惩罚", "系统流钩子"),
    ]
    for pattern, label in hook_patterns:
        matches = re.findall(pattern, text)
        if matches and len(matches) >= 2:
            hooks_found.append(label)

    # 搜索金手指特征
    gf_patterns = [
        (r"系统|面板|属性|技能|等级|经验", "系统面板型"),
        (r"穿越|重生|醒来|回到|过去|上一世", "重生穿越型"),
        (r"传承|秘籍|功法|修炼|丹田", "功法传承型"),
        (r"戒指|项链|手镯|宝物|神器|奇物", "宝物型"),
        (r"天赋|血脉|体质|觉醒|异能", "天赋型"),
    ]
    for pattern, label in gf_patterns:
        if re.search(pattern, text):
            golden_finger_candidates.append(label)
            if len(golden_finger_candidates) >= 3:
                break

    # 估算节奏
    avg_para_len = sum(len(p) for p in paragraphs) / max(1, len(paragraphs))
    if avg_para_len < 80:
        rhythm = "快节奏（短段落为主，适合爽文/都市文）"
    elif avg_para_len < 200:
        rhythm = "中等节奏（段落适中，适合玄幻/系统流）"
    else:
        rhythm = "慢节奏（长段落为主，适合世界观厚重的作品，需注意开篇别太慢）"

    # 估算字数
    char_count = sum(len(p) for p in paragraphs)

    return {
        "title": title,
        "estimated_chapters": max(1, chapter_count),
        "estimated_words": char_count,
        "rhythm": rhythm,
        "hooks_detected": hooks_found if hooks_found else ["未检测到明显钩子模式——建议加强开篇悬念"],
        "golden_finger_style": golden_finger_candidates[:3] if golden_finger_candidates else ["未检测到"],
        "avg_paragraph_length": round(avg_para_len),
        "suggestion": _suggest_opening_improvement(hooks_found, rhythm, paragraphs[:3]),
    }


def _suggest_opening_improvement(hooks: list[str], rhythm: str, first_paras: list[str]) -> str:
    """根据分析结果给出开篇改进建议"""
    if not hooks:
        return ("⚡ 开篇缺钩子——第一段就要让读者产生'然后呢？'的感觉。"
                "建议第一句用悬念/反常事件/对话开头。")
    if len(hooks) >= 2:
        return "✅ 钩子模式丰富，开篇悬念感不错。继续保持！"
    return "💡 开篇有基本钩子，可以考虑在每章结尾再增加一个悬念来提升追读率。"


def refine_idea(
    premise: str = "",
    genre: str = "",
    golden_finger_idea: str = "",
) -> dict[str, Any]:
    """脑洞完善：将一句话灵感扩展为核心设定体系"""
    # 如果没给分类，尝试从梗概推断
    if not genre and premise:
        if re.search(r"系统|面板|任务|奖励", premise):
            genre = "系统流"
        elif re.search(r"重生|穿越|回到|醒来.*年前", premise):
            genre = "重生穿越"
        elif re.search(r"规则|怪谈|诡异|禁忌", premise):
            genre = "规则怪谈"
        elif re.search(r"反套路|迪化|误会|脑补", premise):
            genre = "脑洞反套路"
        else:
            genre = "都市系统流"

    guide = GENRE_GUIDES.get(genre, {})
    prompt_questions = [
        "主角是谁？（姓名、身份、一个核心矛盾）",
        guide.get("key_question", "这个故事的独特卖点是什么？"),
        "反派/阻碍是什么？（没有反对力量就没有故事张力）",
        "主角有什么缺陷？（完美的角色不吸引人）",
        "结局方向是什么？（不需要细节，只需要一个方向感）",
    ]

    setting = CoreSetting(
        premise=premise or "（请填写一句话梗概）",
        golden_finger=golden_finger_idea or "（请描述主角的特殊能力/优势）",
        golden_finger_cost="（这个能力有什么代价/限制？没有代价的能力会让读者失去紧张感）",
    )

    return {
        "genre": genre,
        "genre_guide": guide,
        "prompt_questions": prompt_questions,
        "golden_finger_examples": guide.get("golden_finger_examples", []),
        "pitfalls": guide.get("pitfalls", []),
        "setting": {
            "premise": setting.premise,
            "golden_finger": setting.golden_finger,
            "golden_finger_cost": setting.golden_finger_cost,
            "target_emotion": "（你想让读者感受到什么？爽/好奇/感动/紧张？）",
            "protagonist_flaw": "（主角有什么性格缺陷？）",
        },
        "next_steps": [
            "用 2-3 句话写下故事开篇的第一个场景",
            "定下金手指的三个限制条件",
            "设计一个让读者开口就说'我靠'的反转点",
        ],
    }


def diagnose_opening(text: str) -> dict[str, Any]:
    """开篇诊断：检查第一章的质量"""
    lines = text.strip().split("\n")
    first_300 = text[:300]
    results: list[dict[str, Any]] = []
    score = 100

    # 基础检测
    if len(first_300) < 100:
        return {"error": "文本太短（少于100字），无法进行有效诊断。请提供至少一段完整开篇。",
                "score": 0, "items": []}

    # 背景说明检测
    exposition_keywords = ["世界分为", "这是一个", "自古以来", "在遥远的",
                           "大陆上", "设定是", "背景是"]
    expos_found = [kw for kw in exposition_keywords if kw in first_300]

    # 钩子检测
    has_dialogue_open = bool(first_300.strip().startswith("\"") or first_300.strip().startswith("300c") or first_300.strip().startswith("300e"))

    # 逐项诊断
    for key, check_desc, fail_msg in OPENING_CHECKLIST:
        passed = True
        detail = ""

        if key == "hook":
            passed = has_dialogue_open or any(
                w in first_300 for w in ["突然", "竟然", "没想到", "？", "！"]
            )
            detail = "开篇有悬念或对话钩子" if passed else fail_msg

        elif key == "exposition":
            passed = len(expos_found) == 0
            detail = "开篇无大段背景说明" if passed else f"检测到说明性文字: {', '.join(expos_found)}。{fail_msg}"

        elif key == "conflict":
            last_para = lines[-1] if lines else ""
            passed = any(w in last_para for w in ["？", "!", "突然", "竟然", "难道"])
            detail = "章末有悬念" if passed else fail_msg

        elif key == "emotion":
            emotion_words = ["愤怒", "紧张", "害怕", "兴奋", "好奇", "震惊", "心疼",
                             "不甘", "憋屈", "爽", "燃"]
            passed = any(w in text[:800] for w in emotion_words)
            detail = "开篇有情绪铺垫" if passed else fail_msg

        elif key == "rhythm":
            para_lens = [len(p) for p in lines[:10] if p.strip()]
            if len(para_lens) >= 3:
                has_variance = max(para_lens) > min(para_lens) * 1.5
                passed = has_variance
                detail = "段落有长短节奏变化" if passed else fail_msg
            else:
                passed = True
                detail = "段落数不足，跳过节奏检测"

        elif key == "character_goal":
            goal_patterns = ["想要", "希望", "必须", "一定要", "要.*为了", "为了"]
            passed = any(re.search(p, text[:800]) for p in goal_patterns)
            detail = "主角目标明确" if passed else fail_msg

        elif key == "showing":
            tell_patterns = ["他/她是", "是一个", "性格", "特点是"]
            passed = not any(p in text[:500] for p in tell_patterns)
            detail = "开篇以展示为主" if passed else fail_msg

        if not passed:
            score = max(0, score - 12)

        results.append({
            "check": check_desc,
            "passed": passed,
            "detail": detail,
        })

    # 额外加分
    if has_dialogue_open:
        score = min(100, score + 8)

    verdict = ""
    if score >= 85:
        verdict = "✅ 开篇质量很好，黄金三章的钩子已经立住了。开始写正文吧！"
    elif score >= 60:
        verdict = "⚡ 开篇基本合格，但还有提升空间。重点看标记了 ❌ 的项目。"
    else:
        verdict = "🔧 开篇需要较多修改。按检查清单逐项优化后再发布。"

    return {
        "score": score,
        "verdict": verdict,
        "items": results,
        "quick_fix": "最快速的改进：把第一章第一句改成对话或一个反常事件" if score < 85 else "",
    }


def get_faq_for_newcomer() -> dict[str, list[dict[str, str]]]:
    """新人FAQ"""
    return {
        "入门": [
            {"q": "完全没写过小说，能写网文吗？", "a": "完全可以！网文门槛很低，会打字、能讲故事、愿意坚持就行。大部分成功作者从零开始。"},
            {"q": "第一本书写什么类型好？", "a": "都市系统流、脑洞反套路、规则怪谈——这三个赛道目前对新人最友好。"},
            {"q": "第一本书应该写多少字？", "a": "80-150万字是合适的区间。不要太短（没积累），不要太长（容易烂尾）。"},
            {"q": "需要先想好整个故事再写吗？", "a": "需要明确：开头3章、前期大纲（30万字）、大致的结局方向。边写边完善是常态。"},
        ],
        "开篇": [
            {"q": "开头应该怎么写？", "a": "忘掉背景介绍。第一句话就要有钩子——对话、反常事件、悬念。读者耐心只有几十秒。"},
            {"q": "什么是黄金三章？", "a": "前三章决定读者留存。核心公式：压情绪→破局→震惊读者。每章结尾留一个'然后呢？'"},
            {"q": "开篇最常犯的错误？", "a": "① 大段世界观铺垫 ② 第一章没有冲突 ③ 主角目标模糊 ④ 只说'他很强'但没展示"},
        ],
        "创作": [
            {"q": "卡文了怎么办？", "a": "① 回看大纲找下一个冲突点 ② 写一个新角色进场 ③ 引爆一个之前埋的伏笔 ④ 跳过当前章先写后面的"},
            {"q": "每天应该写多少？", "a": "新人建议日更2000-4000字。质量>数量，但断更最致命。"},
            {"q": "AI写的小说能签约吗？", "a": "平台在严打纯AI水文。合规用法：AI辅助构思+大纲+润色，核心情节和文笔需要人工。燃灯的设计就是这种'人机协作'模式。"},
        ],
    }


# ── CLI 入口 ───────────────────────────────────────────────

def main():
    import sys

    if len(sys.argv) < 2:
        print("用法: python creation_engine.py [market|dissect|idea|diagnose|faq] [参数]")
        return 1

    cmd = sys.argv[1]

    if cmd == "market":
        platform = sys.argv[2] if len(sys.argv) > 2 else "默认"
        for item in analyze_market(platform):
            print(f"\n📊 {item['genre']}")
            print(f"   流量: {item['traffic']} | 竞争: {item['competition']} | 新人: {item['newcomer']}")
            print(f"   💡 {item['tip']}")

    elif cmd == "dissect":
        if len(sys.argv) < 3:
            print("请提供文本文件路径: python creation_engine.py dissect <文件路径>")
            return 1
        text = Path(sys.argv[2]).read_text(encoding="utf-8")
        result = dissect_book(text, Path(sys.argv[2]).name)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == "faq":
        faq = get_faq_for_newcomer()
        for category, items in faq.items():
            print(f"\n## {category}")
            for item in items:
                print(f"  ❓ {item['q']}")
                print(f"  💬 {item['a']}\n")

    elif cmd == "idea":
        premise = sys.argv[2] if len(sys.argv) > 2 else ""
        result = refine_idea(premise=premise)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == "diagnose":
        if len(sys.argv) < 3:
            print("请提供文本文件路径: python creation_engine.py diagnose <文件路径>")
            return 1
        text = Path(sys.argv[2]).read_text(encoding="utf-8")
        result = diagnose_opening(text)
        print(f"综合得分: {result['score']}/100")
        print(f"判定: {result['verdict']}")
        for item in result["items"]:
            status = "✅" if item["passed"] else "❌"
            print(f"  {status} {item['check']}")
            if not item["passed"]:
                print(f"     → {item['detail']}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

# ── 高级拆书：多本+融合 ─────────────────────────────────────

def dissect_book_deep(text: str, title: str = "未命名作品") -> dict[str, Any]:
    """深度拆书：在基础分析上增加章节级拆解"""
    result = dissect_book(text, title)
    # 按章节分割增强分析
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    chapters: list[dict[str, Any]] = []
    chapter_buf: list[str] = []
    chapter_num = 0

    for line in lines:
        if re.match(r"^(第[一二三四五六七八九十百千\d]+[章回节卷]|Chapter\s*\d+|Ch\.?\s*\d+|Vol\.?\s*\d+\s*Ch|^\d+[\.\-、]\s|^0?\d+[\s\.]|[Cc][Hh]\s*\d+)", line, re.IGNORECASE):
            if chapter_buf and chapter_num > 0:
                chapters.append(_analyze_chapter("\n".join(chapter_buf), chapter_num))
            chapter_num += 1
            chapter_buf = [line]
        else:
            chapter_buf.append(line)

    if chapter_buf and chapter_num > 0:
        chapters.append(_analyze_chapter("\n".join(chapter_buf), chapter_num))

    result["chapters_analyzed"] = len(chapters)
    result["chapter_details"] = chapters[:20]  # 最多20章
    result["type"] = "deep"
    return result


def _analyze_chapter(text: str, num: int) -> dict[str, Any]:
    """单章分析"""
    words = len(text)
    hooks = []
    if re.search(r"突然|忽然|竟然|没想到|难道|原来", text):
        hooks.append("转折")
    if re.search(r"\?[^？]*$", text.strip()[-50:]):
        hooks.append("悬念结尾")
    if re.search(r"系统|任务|奖励|惩罚|升级|突破", text):
        hooks.append("系统驱动")
    return {
        "chapter": num,
        "words": words,
        "hooks": hooks or ["无明显钩子"],
        "key_event": _extract_key_event(text),
    }


def _extract_key_event(text: str) -> str:
    """提取关键事件摘要"""
    sentences = re.split(r"[。！？]", text)
    for s in sentences[:10]:
        s = s.strip()
        if len(s) > 15 and any(w in s for w in ["发现", "获得", "遇到", "击败", "突破", "觉醒", "触发"]):
            return s[:60]
    return "未见明显关键事件"


def merge_dissections(books: list[dict[str, Any]]) -> dict[str, Any]:
    """融合多本书的拆解结果，提取共性"""
    if not books:
        return {"error": "请至少提供一本书的拆解结果"}
    if len(books) < 2:
        return {"error": "至少需要2本书才能进行融合分析", "single": books[0]}

    # 汇总钩子模式
    all_hooks: list[str] = []
    all_gf: list[str] = []
    all_titles: list[str] = []
    rhythms: list[str] = []
    total_words = 0

    for b in books:
        all_titles.append(b.get("title", "?"))
        total_words += b.get("estimated_words", 0)
        for h in (b.get("hooks_detected") or []):
            if h not in all_hooks:
                all_hooks.append(h)
        for g in (b.get("golden_finger_style") or []):
            if g not in all_gf:
                all_gf.append(g)
        rhythms.append(b.get("rhythm", ""))

    # 钩子共性
    hook_common = [h for h in all_hooks if sum(1 for b in books if h in (b.get("hooks_detected") or [])) >= max(2, len(books) // 2)]

    # 金手指共性
    gf_common = [g for g in all_gf if sum(1 for b in books if g in (b.get("golden_finger_style") or [])) >= max(2, len(books) // 2)]

    # 节奏统计
    fast = sum(1 for r in rhythms if "快节奏" in r)
    mid = sum(1 for r in rhythms if "中等" in r)
    slow = len(books) - fast - mid
    dominant_rhythm = "快节奏" if fast >= mid and fast >= slow else "中等节奏" if mid >= fast and mid >= slow else "慢节奏"

    return {
        "type": "merged",
        "book_count": len(books),
        "books": all_titles,
        "total_words": total_words,
        "common_hook_patterns": hook_common,
        "common_golden_fingers": gf_common,
        "dominant_rhythm": dominant_rhythm,
        "rhythm_breakdown": f"快:{fast} 中:{mid} 慢:{slow}",
        "all_hooks": all_hooks,
        "all_golden_fingers": all_gf,
        "differences": _diff_analysis(books),
        "suggestion": _merge_suggestion(books, hook_common, gf_common, dominant_rhythm),
    }



def _diff_analysis(books: list[dict]) -> list[dict]:
    """差异化分析：每本书的独特卖点"""
    diffs = []
    for b in books:
        title = b.get("title", "?")
        unique_hooks = [h for h in (b.get("hooks_detected") or []) 
                       if sum(1 for o in books if o != b and h in (o.get("hooks_detected") or [])) == 0]
        unique_gf = [g for g in (b.get("golden_finger_style") or [])
                    if sum(1 for o in books if o != b and g in (o.get("golden_finger_style") or [])) == 0]
        diffs.append({
            "title": title,
            "unique_hooks": unique_hooks,
            "unique_golden_fingers": unique_gf,
            "words": b.get("estimated_words", 0),
            "target": _suggest_target(title, b),
        })
    return diffs


def _suggest_target(title: str, book: dict) -> str:
    """根据拆解结果建议目标读者"""
    hooks = book.get("hooks_detected", [])
    rhythm = book.get("rhythm", "")
    if "系统流" in str(hooks): return "喜欢升级打怪爽文的男性读者（18-30岁）"
    if "规则" in title.lower(): return "喜欢烧脑解谜、对猎奇题材感兴趣的年轻读者"
    if "重生" in title or "穿越" in title: return "喜欢爽文节奏、对'逆袭改变人生'有共鸣的读者"
    if "快节奏" in rhythm: return "喜欢快节奏、碎片化阅读的手机用户"
    return "对快节奏网文有阅读习惯的年轻读者"

def _merge_suggestion(books: list[dict], hooks: list[str], gfs: list[str], rhythm: str) -> str:
    parts = [f"📚 从 {len(books)} 本书中提炼的共性规律：\n"]
    if hooks:
        parts.append(f"🎣 共同钩子模式: {'、'.join(hooks)}——这些是最有效的抓读者手段")
    if gfs:
        parts.append(f"⚡ 共同金手指类型: {'、'.join(gfs)}——读者验证过的爽点引擎")
    parts.append(f"🎵 主流节奏: {rhythm}")
    parts.append(f"\n💡 建议: 在你的作品中至少包含其中 2 种钩子模式 + 1 种金手指类型，并匹配主流节奏。")
    return "\n".join(parts)


# ── 多书批量拆解 ─────────────────────────────────────────────

def dissect_multi_books(books: list[dict[str, str]]) -> dict[str, Any]:
    """批量拆解多本书"""
    results = []
    for b in books:
        title = b.get("title", "未命名")
        text = b.get("text", "")
        if text.strip():
            results.append(dissect_book_deep(text, title) if len(text) > 5000 else dissect_book(text, title))
    merged = merge_dissections(results) if len(results) >= 2 else {}
    return {
        "individual": results,
        "count": len(results),
        "merged": merged,
    }

# ── 7 & 8: 保存到项目 + 大纲生成 + EPUB + 角色模板 ─────────────────

def save_wizard_result(project_root: str, result_type: str, data: dict, title: str = "") -> dict:
    """将向导结果保存到项目文件"""
    from pathlib import Path
    root = Path(project_root)
    out_dir = root / "data" / "wizard_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = __import__("time").strftime("%Y%m%d_%H%M%S")
    filename = f"{result_type}_{ts}.md"
    filepath = out_dir / filename

    lines = [f"# {result_type}: {title}", f"*生成时间: {ts}*", ""]
    if result_type == "dissect":
        lines.append(f"**书名**: {data.get('title', '?')}")
        lines.append(f"**字数**: {data.get('estimated_words', 0)}")
        lines.append(f"**节奏**: {data.get('rhythm', '?')}")
        lines.append(f"**钩子**: {', '.join(data.get('hooks_detected', []))}")
        lines.append(f"**金手指**: {', '.join(data.get('golden_finger_style', []))}")
        if data.get("chapter_details"):
            lines.append("\n## 分章拆解")
            for ch in data["chapter_details"]:
                lines.append(f"- Ch{ch['chapter']}: {ch['words']}字 | {', '.join(ch.get('hooks',[]))} | {ch.get('key_event','')}")
    elif result_type == "idea":
        s = data.get("setting", {})
        lines.append(f"**分类**: {data.get('genre', '?')}")
        lines.append(f"**梗概**: {s.get('premise', '')}")
        lines.append(f"**金手指**: {s.get('golden_finger', '')}")
        lines.append(f"**代价**: {s.get('golden_finger_cost', '')}")
        lines.append(f"**情绪**: {s.get('target_emotion', '')}")
    elif result_type == "opening":
        lines.append(f"**综合得分**: {data.get('score', 0)}/100")
        lines.append(f"**判定**: {data.get('verdict', '')}")
        for item in data.get("items", []):
            status = "✅" if item.get("passed") else "❌"
            lines.append(f"- {status} {item.get('check', '')}")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return {"ok": True, "path": str(filepath.relative_to(root)), "filename": filename}


CHARACTER_TEMPLATES = {
    "系统流": {
        "name": "（填写）",
        "identity": "身份：普通/底层，给读者代入感",
        "goal": "短期：利用系统改善处境 | 长期：站在巅峰/改变世界",
        "flaw": "自卑/冲动/过于谨慎——让角色有成长空间",
        "golden_finger": "系统（签到/任务/反套路）",
        "relationship_anchor": "一个见证主角变化的人（朋友/同事/网友）",
    },
    "重生穿越": {
        "name": "（填写）",
        "identity": "前世身份 → 今世身份（制造落差）",
        "goal": "弥补前世遗憾 / 阻止灾难 / 改变命运",
        "flaw": "带着前世记忆的傲慢 / 过于依赖先知导致蝴蝶效应",
        "golden_finger": "先知记忆+现代知识/技能",
        "relationship_anchor": "前世亏欠的人 / 今世要保护的人",
    },
    "规则怪谈": {
        "name": "（填写）",
        "identity": "普通人 / 特殊体质（能看见隐藏规则）",
        "goal": "活下去 / 通关 / 破解规则背后真相",
        "flaw": "好奇心过强 / 不信任他人 / 过度谨慎",
        "golden_finger": "规则提示 / 免疫一次惩罚 / 规则漏洞发现",
        "relationship_anchor": "第一个遇到的同伴（可能背叛或牺牲）",
    },
    "默认": {
        "name": "（填写）",
        "identity": "填一个让读者能代入的身份",
        "goal": "短期目标和长期目标的冲突",
        "flaw": "至少一个性格缺陷（完美角色最无聊）",
        "golden_finger": "主角的特殊能力/优势",
        "relationship_anchor": "对主角最重要的人",
    },
}


def get_character_guide(genre: str = "默认") -> dict:
    """获取角色创建引导"""
    tmpl = CHARACTER_TEMPLATES.get(genre, CHARACTER_TEMPLATES["默认"])
    return {
        "genre": genre,
        "template": tmpl,
        "tips": [
            "名字是第一印象——选一个让人记住的名字",
            "缺陷比优点重要——不完美的角色才有成长空间",
            "给角色一个'口头禅'或'习惯动作'，立竿见影",
            "关系锚点：至少有一个角色能让主角展现软肋",
        ],
    }


def generate_outline_from_idea(premise: str, genre: str = "") -> dict:
    """从脑洞生成大纲框架"""
    # 基于梗概推断篇章结构
    arcs = _estimate_arcs(premise, genre)
    return {
        "title_hook": _gen_title_hook(premise),
        "tagline": premise[:80],
        "arcs": arcs,
        "total_chapters_estimate": sum(a["chapters"] for a in arcs),
        "first_chapter_hook": _gen_first_chapter_hook(premise, arcs[0] if arcs else {}),
        "writing_tip": "大纲是地图不是牢笼,写到30%可以根据实际情况调整后面的走向。",
    }


def _estimate_arcs(premise: str, genre: str) -> list[dict]:
    """估算篇章结构"""
    # 默认3篇结构
    arcs = [
        {"name": "起·入局", "chapters": 30, "goal": "主角获得金手指/穿越,适应新环境,建立初步人际关系,完成第一次小爆发",
         "key_event": "第一个小高潮（打脸/突破/获得认可）"},
        {"name": "承·发展", "chapters": 50, "goal": "主角深入世界观,遭遇第一道真正的阻碍,能力和心性双重成长",
         "key_event": "中段重大转折（失去重要的人/发现世界真相/遭遇宿敌）"},
        {"name": "转合·收官", "chapters": 40, "goal": "所有伏笔开始回收,主角面对最终挑战,完成角色弧光",
         "key_event": "最终决战/最终揭秘,给出让读者满意的结局"},
    ]
    if "短篇" in premise or len(premise) < 20:
        arcs = [{"name": "全篇", "chapters": 15, "goal": "起承转合压缩在15章", "key_event": "结尾反转"}]
    return arcs


def _gen_title_hook(premise: str) -> str:
    """生成书名建议"""
    keywords = ["系统", "穿越", "重生", "废柴", "签到", "规则", "修真", "都市"]
    found = [k for k in keywords if k in premise]
    if "签到" in premise: return "《签到XXX天后,我XXX了》"
    if "系统" in premise: return "《我的XXX系统》"
    if "重生" in premise or "穿越" in premise: return "《重生XXX:这一世XXX》"
    if found: return f"《{found[0]}之XXX》"
    return "《XXX》（根据你的灵感自定义）"


def _gen_first_chapter_hook(premise: str, first_arc: dict) -> str:
    """生成第一章钩子建议"""
    if "系统" in premise:
        return f"开篇钩子: 主角在人生最低谷→系统激活→{first_arc.get('key_event','第一次用系统能力改变现状')}。第一句用系统提示音开头以最快建立世界观。"
    if "重生" in premise or "穿越" in premise:
        return f"开篇钩子: 一觉醒来发现回到X年前→利用前世记忆做第一件事→{first_arc.get('key_event','改变第一个关键事件')}。用认知落差制造爽感。"
    return f"开篇钩子: 主角的普通生活被打破→遇见改变命运的契机→{first_arc.get('key_event','')}"


# ── 5: EPUB 支持 ──────────────────────────────────────────────

def extract_text_from_epub(content_or_path, is_bytes: bool = False) -> dict:
    """从 EPUB 文件或二进制内容提取纯文本"""
    if is_bytes:
        try:
            from zipfile import ZipFile
            import io
            data = content_or_path if isinstance(content_or_path, bytes) else content_or_path.encode('latin-1')
            zf = ZipFile(io.BytesIO(data))
            return _parse_epub_zip(zf)
        except Exception as e:
            return {"error": f"EPUB 解析失败: {str(e)[:100]}"}

    # Filepath mode (fallback)

def _parse_epub_zip(zf) -> dict:
    """通用 EPUB zip 解析"""
    import re
    text_parts = []
    for name in zf.namelist():
        if name.endswith(('.xhtml', '.html', '.htm', '.xml')):
            with zf.open(name) as f:
                content = f.read().decode('utf-8', errors='ignore')
                cleaned = re.sub(r'<[^>]+>', '\n', content)
                cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
                if cleaned:
                    text_parts.append(cleaned)
    full_text = '\n\n'.join(text_parts)
    return {
        "ok": True,
        "text": full_text,
        "char_count": len(full_text),
        "paragraphs": len(text_parts),
    }

    """从 EPUB 文件提取纯文本"""
    from pathlib import Path
    path = Path(filepath)
    if not path.exists():
        return {"error": f"文件不存在: {filepath}"}
    if not path.suffix.lower() == ".epub":
        return {"error": "仅支持 .epub 格式"}

    try:
        from zipfile import ZipFile
        from xml.etree import ElementTree as ET

        text_parts = []
        with ZipFile(path, 'r') as zf:
            for name in zf.namelist():
                if name.endswith(('.xhtml', '.html', '.htm')):
                    with zf.open(name) as f:
                        try:
                            tree = ET.fromstring(f.read())
                            ns = {'x': 'http://www.w3.org/1999/xhtml'}
                            # Extract all text
                            for elem in tree.iter():
                                if elem.text and elem.text.strip():
                                    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                                    if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'div'):
                                        text_parts.append(elem.text.strip())
                        except Exception:
                            continue

            # Fallback: try plain text extraction from HTML
            if not text_parts:
                for name in zf.namelist():
                    if name.endswith(('.xhtml', '.html', '.htm')):
                        with zf.open(name) as f:
                            content = f.read().decode('utf-8', errors='ignore')
                            # Simple strip tags
                            cleaned = re.sub(r'<[^>]+>', '\n', content)
                            cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
                            text_parts.append(cleaned)

        full_text = '\n\n'.join(text_parts)
        return {
            "ok": True,
            "title": path.stem,
            "text": full_text,
            "char_count": len(full_text),
            "paragraphs": len(text_parts),
        }
    except ImportError:
        return {"error": "EPUB 解析需要 zipfile 和 xml 库（Python 标准库自带）"}
    except Exception as e:
        return {"error": f"EPUB 解析失败: {str(e)[:100]}"}


# ── 7: AI 深度拆书 ────────────────────────────────────────────

def ai_deep_dissect(text: str, title: str = "", llm_client=None) -> dict:
    """AI 深度拆书: 调用 LLM 进行深度分析
    
    需要传入 llm_client (openai-compatible client)。如无 client 则降级为本地分析。
    """
    if not llm_client:
        result = dissect_book_deep(text, title)
        result["note"] = "本地分析模式（未提供 LLM）"
        return result

    # 截取前6000字符避免超token
    sample = text[:6000]

    prompt = f"""你是一位专业的网文编辑。请分析以下小说片段，用 JSON 格式返回:

{{
  "title": "书名",
  "hook_quality": "开篇钩子评分(1-10)",
  "hook_reason": "为什么这个钩子有效/无效 (50字内)",
  "golden_finger": "金手指类型和分析 (50字内)",
  "pacing_score": "节奏评分(1-10)",
  "character_appeal": "主角魅力点 (50字内)",
  "emotion_curve": "情绪走向分析 (50字内)",
  "market_potential": "市场潜力评估 (50字内)",
  "writing_quality": "文笔评分(1-10)",
  "improvement": "最应该改进的1-2个点 (80字内)"
}}

小说片段:
{sample[:4000]}"""

    try:
        import os
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        response = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800,
        )
        content = response.choices[0].message.content or "{}"
        # Try to extract JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            ai_result = json.loads(json_match.group())
            ai_result["title"] = title or ai_result.get("title", "未知")
            ai_result["type"] = "ai_deep"
            ai_result["estimated_words"] = len(text)
            return ai_result
    except Exception as e:
        pass

    # Fallback to local
    result = dissect_book_deep(text, title)
    result["note"] = "AI分析失败，降级为本地分析"
    return result


# ── 8: AI 仿写生成 ────────────────────────────────────────────

def ai_style_imitate(reference_text: str, premise: str, style: str = "", llm_client=None) -> dict:
    """AI 仿写: 基于参考作品风格, 用给定梗概生成一段开篇"""
    if not llm_client:
        return {"error": "仿写需要 LLM 客户端, 请先配置环境变量中的 LLM_API_KEY"}

    ref_sample = reference_text[:2000]

    prompt = f"""你是小说仿写专家。学习以下参考文风（节奏、句式、描写方式），然后用这个风格写一段约 300 字的小说开篇。

【参考风格】
{ref_sample}

【要写的故事】
{premise}

要求:
1. 模仿参考文的节奏和句式(不模仿具体内容)
2. 必须有钩子——第一句话就抓人
3. 写 300 字左右
4. 不要用'微微一笑''眼中闪过一丝'等 AI 套话

直接输出开篇内容,不需要任何说明。"""

    try:
        import os
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        response = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=600,
        )
        content = response.choices[0].message.content or ""
        return {"ok": True, "generated_text": content.strip(), "style": style or "参考风格"}
    except Exception as e:
        return {"error": f"仿写失败: {str(e)[:100]}"}

# ── 作者人设系统 ────────────────────────────────────────────

AUTHOR_PERSONA_DIMENSIONS = {
    "identity": {
        "label": "① 我是谁",
        "fields": {
            "pen_name": {"label": "笔名/代号", "placeholder": "如：荒野小说家"},
            "author_type": {"label": "我是哪种作者", "placeholder": "讲故事的人 / 世界建筑师 / 情感挖掘者 / 思想实验者", "type": "select", "options": ["讲故事的人", "世界建筑师", "情感挖掘者", "思想实验者"]},
            "manifesto": {"label": "一句话创作宣言", "placeholder": "如：我想写让读者半夜睡不着觉的故事"},
        }
    },
    "creative_domain": {
        "label": "② 我写什么",
        "fields": {
            "primary_genre": {"label": "主类型", "placeholder": "都市 / 玄幻 / 科幻 / 悬疑 / 言情"},
            "eternal_themes": {"label": "我永远写不腻的主题", "placeholder": "如：孤独、权力与人性、命运的反叛"},
            "tropes_i_hate": {"label": "我绝不会用的套路", "placeholder": "如：无脑倒贴、系统万能、强行降智"},
        }
    },
    "language": {
        "label": "③ 我的语言习惯",
        "fields": {
            "sentence_style": {"label": "句式偏好", "placeholder": "短句为主 / 绵长细腻 / 干净克制", "type": "select", "options": ["短句为主，偶尔长句", "绵长细腻，娓娓道来", "干净克制，惜字如金", "多变，视场景而定"]},
            "dialogue_style": {"label": "对话风格", "placeholder": "短对话+潜台词 / 机锋交锋 / 长段独白", "type": "select", "options": ["短对话+大量潜台词", "机锋交锋，言语较量", "长段独白，直抒胸臆", "各角色说话风格完全不同"]},
            "forbidden_words": {"label": "禁用词/句式", "placeholder": "如：突然、只见、他的眼中闪过一丝"},
            "narrative_voice": {"label": "叙述语气", "placeholder": "悲悯 / 讽刺 / 热血 / 冷峻 / 幽默", "type": "select", "options": ["悲悯", "讽刺", "热血", "冷峻", "幽默", "温暖"]},
        }
    },
    "rhythm": {
        "label": "④ 我的节奏",
        "fields": {
            "chapter_words": {"label": "每章目标字数", "placeholder": "如：3000", "type": "number"},
            "closing_style": {"label": "章尾风格", "placeholder": "悬念钩子 / 情感余韵 / 戛然而止", "type": "select", "options": ["悬念钩子（让读者想翻页）", "情感余韵（不说话，让读者感受）", "戛然而止（突然断在关键时刻）", "行动决定（主角做出选择，下一章展开）"]},
            "breather": {"label": "高潮后是否有喘息章", "placeholder": "", "type": "select", "options": ["必有日常/过渡章调剂", "直接推进，不废话", "偶尔，看情况"]},
        }
    },
    "characters": {
        "label": "⑤ 我的人物观",
        "fields": {
            "protagonist_style": {"label": "主角人设", "placeholder": "有缺陷的英雄 / 成长型 / 反英雄", "type": "select", "options": ["有缺陷的英雄（有弱点但本质好）", "反英雄（灰色地带，亦正亦邪）", "成长型（从弱到强，伴随成长曲线）", "立体传统主角"]},
            "antagonist_style": {"label": "反派风格", "placeholder": "有魅力的反派 / 立场不同 / 纯粹恶", "type": "select", "options": ["有魅力的反派（读者会同情）", "立场不同没有对错", "纯粹恶（简单直接的威胁）"]},
            "character_depth": {"label": "配角深度", "placeholder": "每个人都有故事 / 配角服务主线", "type": "select", "options": ["每个人都有完整故事", "配角服务于主线", "只有主角重要"]},
        }
    },
    "emotion": {
        "label": "⑥ 我的情感调色盘",
        "fields": {
            "dominant_tone": {"label": "主情绪基调", "placeholder": "热血 / 苍凉 / 温暖 / 悬疑 / 爽", "type": "select", "options": ["热血燃", "苍凉悲", "温暖治愈", "悬疑惊悚", "爽快直接"]},
            "humor": {"label": "幽默程度", "placeholder": "冷幽默 / 无厘头 / 没有 / 人物自带喜感", "type": "select", "options": ["冷幽默（旁观者的毒舌）", "无厘头（意想不到的搞笑）", "没有幽默（偏严肃）", "人物自带喜感"]},
            "romance": {"label": "感情线", "placeholder": "有但克制 / 主线 / 不重要", "type": "select", "options": ["有但克制（暗线为主）", "是主线之一", "不重要", "多角纠葛"]},
        }
    },
    "ambition": {
        "label": "⑦ 我的野心",
        "fields": {
            "scale": {"label": "故事格局", "placeholder": "一个人 / 一群人 / 一个世界", "type": "select", "options": ["一个人的故事", "一群人的史诗", "一个世界的编年史"]},
            "reader_promise": {"label": "给读者的承诺", "placeholder": "如：60%爽文节奏+30%深度思考+10%泪点"},
            "personal_stakes": {"label": "我为什么非得写这个故事", "placeholder": "这个故事对你来说意味着什么？"},
        }
    },
    "boundaries": {
        "label": "⑧ 我的底线",
        "fields": {
            "never": {"label": "我绝不会写", "placeholder": "如：主角光环随意解围、女性角色工具化"},
            "hard_no_phrases": {"label": "绝不用这些表达", "placeholder": "如：他的眼中闪过一丝、谁也没想到、微微一笑"},
        }
    },
}


def get_persona_template() -> dict:
    """获取作者人设模板"""
    return {
        "dimensions": AUTHOR_PERSONA_DIMENSIONS,
        "tips": [
            "不用每一项都填——先填前 4 项就够了",
            "写的过程中可以随时回来改，人设跟着你的创作一起成长",
            "填的越具体，AI 生成的文字越像'你'在写",
        ],
    }


def build_persona_context(persona_data: dict) -> str:
    """将人设转化为 AI 创作上下文"""
    lines = ["## 🖊️ 作者人设约束\n"]
    map_labels = {
        "identity": ("我是谁", ["pen_name", "author_type", "manifesto"]),
        "creative_domain": ("创作领域", ["primary_genre", "eternal_themes"]),
        "language": ("语言习惯", ["sentence_style", "dialogue_style", "narrative_voice"]),
        "rhythm": ("节奏", ["chapter_words", "closing_style"]),
        "emotion": ("情感基调", ["dominant_tone"]),
    }
    for dim_key, (label, fields) in map_labels.items():
        dim = persona_data.get(dim_key, {})
        items = []
        for f in fields:
            val = dim.get(f, "")
            if val:
                items.append(val)
        if items:
            lines.append(f"**{label}**: {'；'.join(items)}")

    # 禁用词
    forbidden = persona_data.get("language", {}).get("forbidden_words", "")
    if forbidden:
        lines.append(f"\n**禁用词/句式**: {forbidden}")

    # 底线
    never = persona_data.get("boundaries", {}).get("never", "")
    hard_no = persona_data.get("boundaries", {}).get("hard_no_phrases", "")
    if never or hard_no:
        lines.append(f"\n**创作底线**: {never}")
        if hard_no:
            lines.append(f"**禁用表达**: {hard_no}")

    return "\n".join(lines)


def save_persona(project_root: str, persona_data: dict) -> dict:
    """保存作者人设到项目"""
    from pathlib import Path
    import yaml
    root = Path(project_root)
    persona_dir = root / "data" / "author"
    persona_dir.mkdir(parents=True, exist_ok=True)
    filepath = persona_dir / "persona.yaml"
    filepath.write_text(yaml.dump(persona_data, allow_unicode=True, default_flow_style=False), encoding="utf-8")
    return {"ok": True, "path": str(filepath.relative_to(root)), "context": build_persona_context(persona_data)}


def load_persona(project_root: str) -> dict:
    """加载已保存的作者人设"""
    from pathlib import Path
    import yaml
    root = Path(project_root)
    filepath = root / "data" / "author" / "persona.yaml"
    if not filepath.exists():
        return {"loaded": False, "template": AUTHOR_PERSONA_DIMENSIONS}
    with filepath.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {"loaded": True, "data": data, "context": build_persona_context(data)}
