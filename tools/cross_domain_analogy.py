"""燃灯 — 跨领域类比设定生成器

v6.0 规格书 Module 5.1：将硬核跨领域知识映射到小说设定中。
利用随机引入的跨界知识（免疫系统、量子力学、博弈论等）生成独特的修炼/魔法体系。
"""

from __future__ import annotations

import os
import random
from typing import Any


# 跨领域知识库
CROSS_DOMAIN_KNOWLEDGE = [
    {
        "domain": "免疫系统",
        "concepts": [
            "T细胞识别并攻击外来入侵者",
            "免疫记忆——一旦感染过就能快速响应",
            "自身免疫病——免疫系统攻击自身",
            "细胞因子风暴——过度反应比感染本身更致命",
        ],
        "genre_hint": "适合修仙、异能、科幻",
    },
    {
        "domain": "量子力学",
        "concepts": [
            "叠加态——粒子同时处于多个状态直到被观测",
            "量子纠缠——两个粒子无论多远都会即时影响对方",
            "观察者效应——观测行为本身改变结果",
            "隧穿效应——粒子穿过看似不可能的势垒",
        ],
        "genre_hint": "适合科幻、脑洞、悬疑",
    },
    {
        "domain": "博弈论",
        "concepts": [
            "囚徒困境——个体最优导致集体最差",
            "纳什均衡——没有人能通过单方面改变策略获益",
            "零和博弈——一人之得即他人之失",
            "重复博弈——长期合作优于短期背叛",
        ],
        "genre_hint": "适合权谋、商战、宫廷",
    },
    {
        "domain": "进化论",
        "concepts": [
            "自然选择——适者生存",
            "趋同进化——不同物种演化出相似特征",
            "红色皇后假说——必须不断进化才能维持相对地位",
            "生态位——每个物种占据独特的生存位置",
        ],
        "genre_hint": "适合末世、异兽、体系升级",
    },
    {
        "domain": "热力学",
        "concepts": [
            "熵增——系统总是趋向无序",
            "能量守恒——能量不灭只转化",
            "热寂——宇宙最终归于热平衡的死亡",
            "麦克斯韦妖——通过信息逆转熵增",
        ],
        "genre_hint": "适合法则体系、世界崩坏、反套路",
    },
    {
        "domain": "信息论",
        "concepts": [
            "香农熵——信息的不确定性度量",
            "信道容量——信息传输的极限",
            "纠错码——在噪声中恢复原始信息",
            "信息不对称——交易中一方比另一方知道更多",
        ],
        "genre_hint": "适合脑洞、策略、谍战",
    },
    {
        "domain": "神经科学",
        "concepts": [
            "神经可塑性——大脑根据经验重塑连接",
            "镜像神经元——看到别人做动作时自己脑中也激活",
            "默认模式网络——白日梦和创造力来源",
            "记忆巩固——睡眠中将短期记忆转为长期",
        ],
        "genre_hint": "适合异能觉醒、精神系、学习体系",
    },
    {
        "domain": "生态学",
        "concepts": [
            "食物链与能量金字塔——能量逐级递减",
            "共生关系——互利共生、寄生、偏利共生",
            "生态演替——群落从先锋到顶级的有序变化",
            "临界点——越过某一阈值后系统不可逆改变",
        ],
        "genre_hint": "适合宗门体系、异世界、末世重建",
    },
]

GENESIS_PROMPT = """你是一位博学的世界观架构师，擅长将硬核跨领域知识映射到小说设定中。

请基于以下信息，创造一个独特的小说修炼/能力体系：

用户基础灵感：{premise}
跨领域知识：{domain} — {concept}
目标类型：{genre_hint}

输出格式：
## 体系名称
（一个有记忆点的名字，如"灵气免疫吞噬体系"）

## 核心映射
（如何将 {domain} 的概念映射到小说世界——80-150字）

## 主角金手指
（基于此体系，主角有什么独特优势）

## 天然冲突
（这个体系自带哪些剧情冲突点——至少3条）

## 同类差异化
（和现有同类型的流行设定有什么本质不同）

要求：设定必须自洽、可写、有新意。"""


def generate_cross_domain_concept(
    premise: str,
    domain: str | None = None,
    llm_client=None,
) -> dict[str, Any]:
    """基于跨领域知识生成世界观概念。

    Args:
        premise: 用户基础灵感（如 "修仙小说"、"都市异能"）
        domain: 指定的知识领域，为空则随机选择
        llm_client: OpenAI 兼容客户端

    Returns:
        {"concept": 生成的设定, "domain": 使用的领域, "mapping": 映射说明}
    """
    # 选择知识领域
    if domain:
        knowledge = next((k for k in CROSS_DOMAIN_KNOWLEDGE if k["domain"] == domain), None)
    else:
        knowledge = random.choice(CROSS_DOMAIN_KNOWLEDGE)

    if not knowledge:
        knowledge = random.choice(CROSS_DOMAIN_KNOWLEDGE)

    concept = random.choice(knowledge["concepts"])

    if llm_client:
        return _llm_genesis(premise, knowledge, concept, llm_client)
    else:
        return _template_genesis(premise, knowledge, concept)


def _llm_genesis(
    premise: str,
    knowledge: dict,
    concept: str,
    client,
) -> dict[str, Any]:
    """使用 LLM 深度生成。"""
    prompt = GENESIS_PROMPT.format(
        premise=premise,
        domain=knowledge["domain"],
        concept=concept,
        genre_hint=knowledge["genre_hint"],
    )

    try:
        model = os.environ.get("LLM_MODEL", "deepseek-chat")
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=1200,
        )
        result = resp.choices[0].message.content or ""
        return {
            "concept": result.strip(),
            "domain": knowledge["domain"],
            "concept_key": concept,
            "genre_hint": knowledge["genre_hint"],
            "used_llm": True,
        }
    except Exception as e:
        return {
            "concept": _template_genesis(premise, knowledge, concept)["concept"],
            "domain": knowledge["domain"],
            "concept_key": concept,
            "used_llm": False,
            "error": str(e)[:100],
        }


def _template_genesis(
    premise: str,
    knowledge: dict,
    concept: str,
) -> dict[str, Any]:
    """本地模板模式。"""
    mapping = f"""## 体系名称
{premise} × {knowledge['domain']} 体系

## 核心映射
将「{knowledge['domain']}」的 "{concept}" 映射到 {premise} 的世界中：
- 原始概念：{concept}
- 小说映射：将这一原理转化为修炼法则 / 世界规则 / 能力设定

## 主角金手指
主角是唯一理解/掌握这一跨领域原理的人，因此在这个体系中拥有天然优势。

## 天然冲突
1. 传统修炼者不理解新体系 → 冲突
2. 体系本身的内在矛盾 → 代价
3. 外部势力想要独占/摧毁这个体系 → 危机

## 同类差异化
区别于传统 {premise} 的套路的本质不同在于引入了 {knowledge['domain']} 的科学原理作为底层逻辑。

💡 配置 LLM_API_KEY 获得 AI 深度跨领域生成。"""

    return {
        "concept": mapping,
        "domain": knowledge["domain"],
        "concept_key": concept,
        "genre_hint": knowledge["genre_hint"],
        "used_llm": False,
    }


def list_available_domains() -> list[dict[str, str]]:
    """列出所有可用的跨领域知识库。"""
    return [
        {
            "domain": k["domain"],
            "genre_hint": k["genre_hint"],
            "concept_count": len(k["concepts"]),
        }
        for k in CROSS_DOMAIN_KNOWLEDGE
    ]


def generate_multi_domain(
    premise: str,
    count: int = 3,
    llm_client=None,
) -> dict[str, Any]:
    """生成多个跨领域设定方案，供用户选择。"""
    domains = random.sample(CROSS_DOMAIN_KNOWLEDGE, min(count, len(CROSS_DOMAIN_KNOWLEDGE)))
    results = []

    for k in domains:
        concept = random.choice(k["concepts"])
        if llm_client:
            r = _llm_genesis(premise, k, concept, llm_client)
        else:
            r = _template_genesis(premise, k, concept)
        results.append(r)

    return {
        "premise": premise,
        "options": results,
        "total": len(results),
    }
