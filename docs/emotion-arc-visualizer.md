# 燃灯 — 情感弧线可视化

> 设计日期: 2026-07-19 | 目标: 逐章标注情绪强度与类型，绘制全卷情感曲线，识别情绪结构中的隐患 | 优先级: P0

---

## 问题定义

网文是情感产业。读者追更不是为了看情节——情节是载体，情感才是读者买单的东西。

```
读者的追更心理模型:
  "这一章让我爽了" → 想追下一章
  "这一章有点无聊" → 再看看
  "最近几章都差不多" → 养着吧
  "我都忘了上次好看是哪章了" → 弃了

核心矛盾: 作者感知不到情感的「边际递减效应」。
         第 50 次「爽点」和第 1 次「爽点」给读者的冲击完全不同，
         但作者在写的时候，体验到的疲劳与读者完全不同步。
```

**情感弧线可视化器**的目标：让作者像看股票 K 线图一样，直观看到自己作品的情感走向——哪里在耗竭读者的情绪资源，哪里给得太少，哪里节奏正要出事。

---

## 一、情绪标注维度

### 1.1 三维标注体系

每章标注三个维度的情绪数据：

```yaml
# 每章情绪标注格式
chapter_emotion:
  chapter_id: 156
  intensity: 7               # 维度 1: 情绪强度 (1-10)
  type: "燃"                 # 维度 2: 情绪类型 (7 种基础类型)
  type_secondary: "爽"       # 副类型（可选，混合情绪时使用）
  reader_pulse:              # 维度 3: 读者心跳曲线向量
    pre_slope: "steep_rise"  # 高潮前斜率: steep_rise | gradual | flat | drop
    post_recovery: "slow"    # 高潮后恢复: quick(1章) | medium(2章) | slow(3+章) | none(无高潮)
    breather_needed: false   # 是否需要喘息章（连续高强度后评估）
```

### 1.2 强度标尺 (1-10)

```yaml
# data/emotion/intensity_scale.yaml
intensity_scale:
  1:  # 极平静
    description: "纯粹日常/过渡/设定展示，无任何冲突"
    examples: ["主角修炼/读书/逛街", "城市风貌描写", "世界观设定铺陈"]
    reader_experience: "在养书/准备跳过"
    max_consecutive: 5           # 最多连续 5 章

  2:  # 轻度日常
    description: "日常中有轻微情绪波动（小幽默、小温馨、小好奇）"
    examples: ["角色间日常对话有俏皮互动", "发现一个小线索", "温馨师徒相处"]
    reader_experience: "放松但不无聊"
    max_consecutive: 8

  3:  # 温和推进
    description: "情节在推进但张力低，有信息量但无紧迫感"
    examples: ["调查/探索/学习新能力", "支线剧情发展", "配角关系演变"]
    reader_experience: "还行，看看后面怎么发展"
    max_consecutive: 10

  4:  # 小波澜
    description: "轻微冲突或情绪波动，读者能感受到「有事要发生」"
    examples: ["小规模战斗（非核心敌人）", "角色间出现分歧", "发现可疑线索"]
    reader_experience: "有点意思了"
    max_consecutive: "无限制（低张力但非乏味）"

  5:  # 中等张力
    description: "冲突正在升级，读者开始担心角色/关心结果"
    examples: ["重要对话（关系转折）", "中规模战斗", "谜团揭示一部分"]
    reader_experience: "在追，想知道接下来"
    max_consecutive: "无限制"

  6:  # 紧张
    description: "冲突达到较高水平，读者有明显的情绪卷入"
    examples: ["核心战斗（非最终）", "重大背叛/真相", "角色面临重大抉择"]
    reader_experience: "看得停不下来"
    max_consecutive: 6

  7:  # 激烈
    description: "情绪接近峰值，读者高度投入"
    examples: ["关键战役的决胜阶段", "重要角色的死亡/觉醒", "压抑后的爆发"]
    reader_experience: "心跳加速"

  8:  # 高光/真高潮
    description: "卷级/书级重大高潮，情绪达到了一个顶峰"
    examples: ["击败本卷大反派", "史诗级战斗/仪式", "累积 50 章的情感爆发"]
    reader_experience: "这一章值得截图发朋友圈"
    per_volume_minimum: 1      # 每卷至少 1 次强度 ≥8

  9:  # 极限情绪
    description: "读者情绪被推到极限——燃到流泪、虐到心痛、甜到尖叫"
    examples: ["主角牺牲/重大蜕变", "等待 300 章的伏笔揭秘", "终极反转"]
    reader_experience: "看完会缓很久"
    per_volume_maximum: 2      # 每卷最多 2 次（多了会麻木）

  10: # 神回
    description: "全书级名场面——看完这章读者会自发安利给朋友"
    examples: ["「我于杀戮之中盛放，亦如黎明中的花朵」级场景"]
    reader_experience: "成为记忆锚点，多年后还会提起"
    per_novel_maximum: 5
```

### 1.3 情绪类型 (7 种基础类型 + 混合)

```yaml
# data/emotion/emotion_types.yaml
emotion_types:

  - id: "燃"
    name: "燃/热血"
    description: "主角突破极限/以弱胜强/团队协作/信念爆发"
    intensity_range: [5, 10]
    reader_reaction: "想跟着喊出来"
    overuse_warning: "连续燃会让读者累——燃需要配日常来缓冲"
    distinct_from:
      - "爽": "燃有情感投入，爽可以纯理性欣赏"
      - "虐": "燃是向上突破，虐是被向下拉扯"

  - id: "虐"
    name: "虐/悲痛"
    description: "失去/牺牲/背叛/命运碾压/无力感"
    intensity_range: [4, 10]
    reader_reaction: "心揪着，想哭"
    prerequisite: "必须有充分的铺垫，否则虐不动"
    overuse_warning: "连续虐 = 读者跑路——虐后必须有「糖」或「燃」来平衡"
    max_consecutive: 3

  - id: "甜"
    name: "甜/温馨"
    description: "角色间的情感升温/默契/关心/守护"
    intensity_range: [1, 6]
    reader_reaction: "姨母笑/嘴角压不下来"
    best_placement: "虐的后面，或者日常间隙中穿插"
    overuse_warning: "纯甜无冲突 = 工业糖精——甜需要张力支撑"

  - id: "悬"
    name: "悬/紧张"
    description: "谜团/危机预感/未知恐惧/等待揭晓"
    intensity_range: [3, 9]
    reader_reaction: "屏住呼吸/疯狂翻下一章"
    prerequisite: "必须前后有呼应的谜面→谜底"
    overuse_warning: "悬念吊太久不揭 = 读者忘记/不关心了"
    max_consecutive_without_reveal: 15  # 15 章不揭谜底 → 警告

  - id: "悲"
    name: "悲/苍凉"
    description: "宏大叙事中的无力感/时代洪流下的个体/宿命的沉重"
    intensity_range: [2, 8]
    reader_reaction: "沉默/心里堵/思考"
    distinct_from:
      - "虐": "悲是个人的被伤害，悲是宏大下的渺小感"
    best_placement: "卷末/重大转折点"
    overuse_warning: "过度悲凉 = 读者觉得压抑不想读了"

  - id: "爽"
    name: "爽/畅快"
    description: "打脸/碾压/收债/反转/长期压抑后的释放"
    intensity_range: [4, 9]
    reader_reaction: "舒服了/终于"
    prerequisite: "必须有足够的「压」才有「爽」——爽的程度 = 压抑的程度 × 释放的合理度"
    overuse_warning: "纯爽无压 = 浮在空中没感觉"
    best_placement: "需要精准计算：什么节点读者最渴望这个爽点"

  - id: "日常"
    name: "日常/过渡"
    description: "角色间的自然互动/世界细节/轻松段落"
    intensity_range: [1, 4]
    reader_reaction: "放松/会心一笑"
    function: "重要的情绪缓冲——没有日常就没有高潮"
    overuse_warning: "日常也需 'micro-tension'，绝对平静的日常 = 无聊"
```

### 1.4 情绪混合规则

```yaml
# data/emotion/mixed_emotions.yaml
# 混合情绪标注规则（一章可能同时有燃+悲、甜+虐等复杂情绪）

mixed_emotion_rules:

  - pair: ["燃", "悲"]
    name: "壮烈"
    description: "在胜利中感受到代价的沉重——最高级的情绪复合体"
    example: "主角击败仇敌，但发现仇敌当年也是被逼的——胜利带着苦涩"

  - pair: ["甜", "虐"]
    name: "刀糖"
    description: "温馨中埋伏了刀子——读者在甜里尝到了苦"
    example: "两人终于牵手，但其中一人只剩三天寿命"

  - pair: ["爽", "悬"]
    name: "悬爽"
    description: "爽了一把但更大的问题随之浮出水面——爽不纯粹，有后续"
    example: "打脸了看不起自己的人，但对方的背景让主角意识到麻烦才刚开始"

  - pair: ["日常", "悲"]
    name: "平淡悲"
    description: "日常中透出一种无力感——比正面写悲更有余韵"
    example: "战胜大反派后，主角回到空荡荡的家，煮了两人份的饭"
```

---

## 二、检测规则

### 2.1 结构性隐患检测

```python
class EmotionArcAnalyzer:
    """情感弧线分析器"""

    def __init__(self, config_path: str):
        self.intensity_scale = self._load("data/emotion/intensity_scale.yaml")
        self.emotion_types = self._load("data/emotion/emotion_types.yaml")
        self.mixed_rules = self._load("data/emotion/mixed_emotions.yaml")

    def check_emotion_plateau(self, chapters: list[dict]) -> list[dict]:
        """
        规则 1: 「情绪平原」检测
        连续 10 章强度波动 < 2 分 → 危险区间

        原理: 读者的情绪需要波动——全是一个调 = 催眠。
              最好的情绪曲线像心电图：有峰有谷，有生命感。
        """
        warnings = []
        window_size = 10

        for i in range(len(chapters) - window_size + 1):
            window = chapters[i:i + window_size]
            intensities = [ch["intensity"] for ch in window]
            variance = max(intensities) - min(intensities)

            if variance < 2:
                start_ch = window[0]["chapter_id"]
                end_ch = window[-1]["chapter_id"]
                avg_intensity = sum(intensities) / len(intensities)

                warnings.append({
                    "type": "emotion_plateau",
                    "severity": "high" if avg_intensity < 3 else "medium",
                    "range": f"ch_{start_ch} - ch_{end_ch}",
                    "message": (
                        f"连续 {window_size} 章情绪强度波动仅 {variance} 分——"
                        f"读者会感觉 '一直是这个调'。"
                    ),
                    "suggestion": (
                        "打破策略:"
                        if avg_intensity < 3:
                            "引入一个意外事件（来信/突然袭击/新角色登场）。"
                        else:
                            "在中等张力段插入一个短暂的情绪低谷（日常/温馨），"
                            "让读者重建对波动的敏感度。"
                    )
                })

        return warnings

    def check_fake_climax(self, chapters: list[dict], vol_id: int) -> list[dict]:
        """
        规则 2: 「假高潮」检测
        每卷至少 1 次强度 ≥8 的「真高潮」，不能全用「打斗」凑数

        原理: 战斗 ≠ 高潮。读者对「又打了一架但什么都没改变」的容忍度很低。
              真高潮 = 情绪上有质的突破（关系转折/真相揭示/角色蜕变）
              假高潮 = 只有场面没有实质的情节推进
        """
        warnings = []
        climax_candidates = [ch for ch in chapters if ch["intensity"] >= 8]

        if not climax_candidates:
            warnings.append({
                "type": "missing_climax",
                "severity": "high",
                "range": f"vol_{vol_id}",
                "message": (
                    f"第 {vol_id} 卷无任何强度 ≥8 的高潮章节——"
                    "读者读完会感到 '这卷好像什么都没发生'。"
                ),
                "suggestion": "确认本卷的「高光时刻」是什么。如果没有，建议重新设计卷末。"
            })
            return warnings

        # 检查高潮质量
        for ch in climax_candidates:
            is_just_fight = (
                ch["emotion_type"] == "燃" and
                not ch.get("has_plot_consequence") and
                not ch.get("has_character_shift") and
                not ch.get("has_revelation")
            )
            if is_just_fight:
                warnings.append({
                    "type": "fake_climax",
                    "severity": "medium",
                    "chapter": ch["chapter_id"],
                    "message": (
                        f"第 {ch['chapter_id']} 章强度 {ch['intensity']} 但仅有战斗场面——"
                        "读者打完就忘了。真高潮需要情节/情感/认知上的突破。"
                    ),
                    "suggestion": (
                        "在战斗中加入一个不可逆的后果:"
                        "角色受伤/失去/获得关键信息/关系改变/一个谜团被揭开。"
                    )
                })

        return warnings

    def check_emotion_burnout(self, chapters: list[dict]) -> list[dict]:
        """
        规则 3: 「情绪透支」检测
        连续 3 章强度 ≥8 → 读者会麻木

        原理: 人的情绪有「不应期」。连续高强度 = 阈值被拉高 =
              后面 9 分的章节读者也只感觉 5 分。
              情绪是珍贵资源，需要合理分配。
        """
        warnings = []
        consecutive_high = 0
        burnout_start = None

        for ch in chapters:
            if ch["intensity"] >= 8:
                if burnout_start is None:
                    burnout_start = ch["chapter_id"]
                consecutive_high += 1
            else:
                if consecutive_high >= 3:
                    warnings.append({
                        "type": "emotion_burnout",
                        "severity": "high",
                        "range": f"ch_{burnout_start} - ch_{ch['chapter_id'] - 1}",
                        "message": (
                            f"连续 {consecutive_high} 章强度 ≥8——"
                            "读者的情绪被透支。后面的高潮将不再有冲击力。"
                        ),
                        "suggestion": (
                            "高强度章节之间必须有「喘息章」:"
                            "1-2 章强度 3-5 的日常/过渡/小温馨。"
                            "让读者的情绪归零，才能再次被推高。"
                        )
                    })
                consecutive_high = 0
                burnout_start = None

        # 边界处理: 如果最后几章连续高强度
        if consecutive_high >= 3:
            warnings.append({
                "type": "emotion_burnout",
                "severity": "high",
                "range": f"ch_{burnout_start} - ch_{chapters[-1]['chapter_id']}",
                "message": (
                    f"连续 {consecutive_high} 章强度 ≥8——"
                    "读者情绪透支，下一章必须降压。"
                ),
                "suggestion": "立即插入 2 章强度 3-4 的过渡。"
            })

        return warnings

    def check_volume_depression(self, current_vol: dict,
                                previous_vol: dict) -> list[dict]:
        """
        规则 4: 卷间对比 — 情绪压抑趋势
        卷 N 整体情绪比卷 1 低 15% → 读者会感到「越来越沉闷」

        原理: 长篇作品的天然趋势是「越来越沉重」（角色成长伴随代价）。
              但读者需要一个平衡——如果情绪持续走低，就变成了阅读负担。
        """
        warnings = []
        current_avg = current_vol["avg_intensity"]
        prev_avg = previous_vol["avg_intensity"]
        vol1_avg = self._get_volume_avg(1)
        delta_from_vol1 = (current_avg - vol1_avg) / vol1_avg * 100

        warning = {}

        if delta_from_vol1 < -15:
            warning["severity"] = "high"
            warning["message"] = (
                f"本卷平均情绪强度 ({current_avg:.1f}) 相比第 1 卷 ({vol1_avg:.1f}) "
                f"下降了 {abs(delta_from_vol1):.0f}%——读者可能感到作品「越来越压抑」。"
            )
            warning["suggestion"] = (
                "策略: 在下卷安排 2-3 个「回到初心」的章节——"
                "让主角体验短暂的胜利/温馨/友情，打破压抑的连续感。"
            )
        elif delta_from_vol1 < -8:
            warning["severity"] = "medium"
            warning["message"] = (
                f"本卷情绪强度相比第 1 卷下降 {abs(delta_from_vol1):.0f}%——"
                "目前仍可控，但需关注趋势。"
            )
            warning["suggestion"] = "下卷至少保持当前水平，不要再降。"

        if warning:
            warnings.append({"type": "volume_depression", **warning})

        # 也检查与上一卷的对比
        delta_from_prev = (current_avg - prev_avg) / prev_avg * 100
        if delta_from_prev < -10:
            warnings.append({
                "type": "volume_drop_sharp",
                "severity": "medium",
                "message": (
                    f"本卷比上卷情绪强度骤降 {abs(delta_from_prev):.0f}%——"
                    "可能是好（暴风雨前的平静）也可能是坏（作者倦怠）。"
                    "请确认意图。"
                )
            })

        return warnings

    def check_emotion_type_distribution(self, chapters: list[dict]) -> list[dict]:
        """
        规则 5: 情绪类型分配检测
        单一类型占比过高 → 读者厌腻
        """
        warnings = []
        total = len(chapters)
        type_counts = {}
        for ch in chapters:
            etype = ch["emotion_type"]
            type_counts[etype] = type_counts.get(etype, 0) + 1

        for etype, count in type_counts.items():
            ratio = count / total

            # 单一类型 >60% → 警告
            if ratio > 0.6:
                warnings.append({
                    "type": "emotion_monotony",
                    "severity": "medium",
                    "emotion_type": etype,
                    "ratio": f"{ratio:.0%}",
                    "message": (
                        f"「{etype}」类型占本卷 {ratio:.0%}——"
                        "单一情绪持续太久读者会腻。"
                    ),
                    "suggestion": (
                        f"建议混入: "
                        + ", ".join(self._get_complementary_types(etype))
                    )
                })

            # 燃 >40% → 特别警告（燃需要配日常）
            if etype == "燃" and ratio > 0.4:
                warnings.append({
                    "type": "燃_过度",
                    "severity": "medium",
                    "message": (
                        f"「燃」占 {ratio:.0%}——没有日常缓冲的燃会变成噪音。"
                        "读者需要安静的时刻来对比出战场的激烈。"
                    ),
                    "suggestion": "每 2-3 章「燃」之后插入 1 章「日常」或「甜」。"
                })

            # 虐 >25% → 严重警告
            if etype == "虐" and ratio > 0.25:
                warnings.append({
                    "type": "虐_过度",
                    "severity": "high",
                    "message": (
                        f"「虐」占 {ratio:.0%}——超过四分之一的内容在虐读者。"
                        "读者需要看到希望，否则会情绪疲劳。"
                    ),
                    "suggestion": "立刻安排 2-3 章「甜」或「爽」来修复读者情绪。"
                })

        return warnings

    def check_recovery_after_climax(self, chapters: list[dict]) -> list[dict]:
        """
        规则 6: 高潮后恢复检测
        高强度后是否有足够缓冲
        """
        warnings = []

        for i, ch in enumerate(chapters):
            if ch["intensity"] >= 8 and i < len(chapters) - 1:
                next_ch = chapters[i + 1]

                # 高潮后下一章仍然高强度
                if next_ch["intensity"] >= 7:
                    warnings.append({
                        "type": "no_recovery",
                        "severity": "medium",
                        "chapter": next_ch["chapter_id"],
                        "message": (
                            f"第 {ch['chapter_id']} 章高潮（强度 {ch['intensity']}）后，"
                            f"下一章强度仍为 {next_ch['intensity']}——"
                            "读者没时间消化高潮。"
                        ),
                        "suggestion": "在高潮后至少给 1 章强度 3-5 的恢复期。"
                    })

                # 高潮后直接掉到死寂（强度下降 >6）
                elif next_ch["intensity"] <= ch["intensity"] - 6:
                    warnings.append({
                        "type": "sharp_drop",
                        "severity": "low",
                        "chapter": next_ch["chapter_id"],
                        "message": (
                            f"高潮后强度骤降 {ch['intensity']} → {next_ch['intensity']}——"
                            "落差太大可能让读者觉得 '突然无聊了'。"
                        ),
                        "suggestion": "在骤降中保留一个小钩子（悬念/新线索），让读者有东西期待。"
                    })

        return warnings
```

### 2.2 全面检测流程

```python
class EmotionArcFullCheck:
    """情感弧线全面检查 —— 卷级触发"""

    def run_all_checks(self, chapters: list[dict],
                       current_vol: dict,
                       previous_vol: dict) -> dict:
        analyzer = EmotionArcAnalyzer()

        results = {
            "emotion_plateau":      analyzer.check_emotion_plateau(chapters),
            "fake_climax":          analyzer.check_fake_climax(chapters, current_vol["id"]),
            "emotion_burnout":      analyzer.check_emotion_burnout(chapters),
            "volume_depression":    analyzer.check_volume_depression(current_vol, previous_vol),
            "type_distribution":    analyzer.check_emotion_type_distribution(chapters),
            "recovery_after_climax": analyzer.check_recovery_after_climax(chapters),
        }

        # 汇总严重性
        severity_count = {"high": 0, "medium": 0, "low": 0}
        for checks in results.values():
            for w in checks:
                severity_count[w["severity"]] += 1

        results["summary"] = {
            "total_warnings": sum(severity_count.values()),
            "by_severity": severity_count,
            "overall_health": self._assess_health(severity_count),
        }

        return results

    def _assess_health(self, severity_count: dict) -> str:
        if severity_count["high"] >= 2:
            return "🔴 情绪结构存在严重隐患，建议在继续写作前修复。"
        elif severity_count["high"] == 1 or severity_count["medium"] >= 3:
            return "🟠 存在需要关注的情绪结构问题。"
        elif severity_count["medium"] >= 1 or severity_count["low"] >= 3:
            return "🟡 总体健康，有小瑕疵。"
        else:
            return "✅ 情绪结构健康。"
```

---

## 三、情感弧线可视化 — Studio 面板设计

### 3.1 面板布局

```
┌──────────────────────────────────────────────────────────────┐
│  燃灯 Studio — 🎭 情感仪表盘                       第 3 卷    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ 全卷情绪曲线 ────────────────────────────────────────┐  │
│  │                                                        │  │
│  │  10 ┤                                          ●        │  │
│  │     │              ●────●                  ●──┘         │  │
│  │   8 ┤         ●───┘      ●────●      ●───┘             │  │
│  │     │    ●───┘                  ●────┘                 │  │
│  │   6 ┤ ●─┘                                               │  │
│  │     │●                                                  │  │
│  │   4 ┤──●   ●─●                      ●─●                │  │
│  │     │  └─●─┘ └─●─●          ●─●─●──┘   └─●─●          │  │
│  │   2 ┤           └─●──●──●──┘                 └─●       │  │
│  │     │                                                  │  │
│  │   0 ┼────┬────┬────┬────┬────┬────┬────┬────┬────      │  │
│  │       0101  0120  0140  0160  0180                     │  │
│  │                                                        │  │
│  │  标注: ● 高潮  ○ 低谷  ◇ 转折  ~ 日常  ⚡ 假高潮       │  │
│  │                                                        │  │
│  │  🔴 第 0112 章 — 假高潮 (强度 8、仅有战斗、无情节突破)  │  │
│  │  🟢 第 0145 章 — 真高潮 (强度 9、伏笔回收 + 角色蜕变)  │  │
│  │  ⚠️  第 0160-0170 — 情绪平原 (10 章波动 <1.5)          │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ 情绪类型分布 ──────────────┐ ┌─ 跨卷对比 ────────────┐  │
│  │                              │ │                        │  │
│  │  燃 ████████████ 38%        │ │  卷1 ████████▌ 6.1     │  │
│  │  虐 ████ 13%                │ │  卷2 ███████▌  5.7     │  │
│  │  甜 ███ 9%                  │ │  卷3 ██████▌   5.2 ⚠️  │  │
│  │  悬 █████ 15%               │ │                        │  │
│  │  爽 ████ 12%                │ │  ↓ -14% vs 卷1         │  │
│  │  日常 ████ 13%              │ │  读者可能觉得压抑       │  │
│  │                              │ │                        │  │
│  └──────────────────────────────┘ └────────────────────────┘  │
│                                                              │
│  ┌─ 人话总结 ────────────────────────────────────────────┐  │
│  │                                                        │  │
│  │  💬 "你的读者现在可能有点累了。                            │  │
│  │       第 3 卷从第 165 章开始持续走低，10 章没有像样        │  │
│  │       的情绪起伏。好消息是：第 145 章的真高潮质量很高       │  │
│  │       ——读者会记住这一刻。                                │  │
│  │       建议在下章来点「爽」的，让读者痛快一把。              │  │
│  │       然后第 4 卷开头需要一个明确的情绪锚点。"             │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ 预警 ────────────────────────────────────────────────┐  │
│  │  ⚠️  高潮后恢复不足: 第 0145 章高潮后，第 0146 章强度 7  │  │
│  │  🔴 情绪平原: ch_0160-0170 (10 章波动 <1.5)             │  │
│  │  ⚠️  假高潮: 第 0112 章仅有战斗、无情节突破              │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  [展开曲线详情]  [导出报告]  [AI 优化建议]  [查看读者情绪预测]  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 交互能力

```yaml
# 情感仪表盘交互功能
dashboard_interactions:
  
  hover_detail:
    - 鼠标悬停任意数据点 → 弹出该章的情绪卡片
    - 卡片内容: 强度/类型/一句话摘要/关键事件
  
  range_select:
    - 拖拽选择曲线区域 → 显示选中区间的统计
    - 统计: 平均强度/波动范围/主要情绪类型/有无隐患
  
  compare_volumes:
    - 选择两个卷号 → 并排对比两条情绪曲线
    - 高亮差异区域
    - 计算结构相似度（节奏是否为作者想要的效果）
  
  prediction_forward:
    - 基于当前情绪趋势 → 预测未来 10 章的情绪走向
    - 标注预测中的高危区域
  
  annotation_mode:
    - 作者在曲线上手动标注: 「这里是故意的」「这里有特殊意图」
    - 手工标注的章节 → 跳过自动告警
  
  chapter_link:
    - 点击数据点 → 直接跳转对应章节的编辑界面
```

---

## 四、YAML 配置

```yaml
# config/emotion_arc.yaml
emotion_arc:
  # 总开关
  enabled: true

  # 标注维度
  annotation:
    dimensions:
      - intensity       # 情绪强度 (1-10)
      - type            # 情绪类型 (燃/虐/甜/悬/悲/爽/日常)
      - type_secondary  # 副类型（混合情绪）
      - reader_pulse    # 读者心跳曲线向量
    
    auto_annotate: true               # 每章写完后自动标注
    manual_override: true             # 允许作者手动修正自动标注
    confidence_threshold: 0.7         # 自动标注置信度阈值（低于此值标记为「需人工确认」）

  # 检测规则
  checks:
    emotion_plateau:                   # 情绪平原
      enabled: true
      window: 10                       # 检测窗口（章）
      variance_threshold: 2            # 波动阈值（分）
    
    fake_climax:                       # 假高潮
      enabled: true
      intensity_threshold: 8           # 强度阈值
      plot_consequence_required: true  # 是否要求有情节后果
      character_shift_required: true   # 是否要求有角色蜕变
    
    emotion_burnout:                   # 情绪透支
      enabled: true
      consecutive_threshold: 3         # 连续高强度阈值
      intensity_threshold: 8
    
    volume_depression:                 # 卷间压抑
      enabled: true
      delta_percent: 15                # 相比卷1的下降阈值（%）
      volume_1_as_baseline: true
    
    type_distribution:                 # 类型分配
      enabled: true
      single_type_max_ratio: 0.6       # 单一类型最大占比
      燃_max_ratio: 0.4
      虐_max_ratio: 0.25
    
    recovery_after_climax:             # 高潮后恢复
      enabled: true
      post_climax_max_intensity: 6     # 高潮后一章最大强度
      sharp_drop_threshold: 6          # 骤降阈值（分）

  # 可视化
  visualization:
    chart:
      type: "line"                     # line | area | candlestick
      color_by: "type"                 # 按类型着色
      annotations: ["高潮", "低谷", "转折", "日常", "假高潮"]
      show_trend_line: true            # 显示移动平均线
      show_volume_boundaries: true     # 显示卷间隔
      interactive: true
    
    dashboard:
      enabled: true
      components:
        - "全卷情绪曲线"
        - "情绪类型分布"
        - "跨卷对比"
        - "人话总结"
        - "预警列表"
    
    export:
      formats: ["svg", "png", "html", "markdown"]
      include_data_table: true

  # 标注数据存储
  storage:
    directory: "data/emotion/"
    per_chapter: "data/emotion/chapters/ch_{id}_emotion.yaml"
    per_volume: "data/emotion/volumes/vol_{id}_emotion.yaml"
    index: "data/emotion/index.yaml"

  # 风格库（参考曲线）
  reference_arcs:
    enabled: true
    library: "data/emotion/reference_arcs.yaml"
    # 预设参考曲线: 「经典热血漫弧线」「虐甜交替弧线」「悬疑递进弧线」等
```

---

## 五、集成示例

### 5.1 在写章流程中接入

```python
# tools/emotion_guard.py
"""
情感弧线守卫 — 嵌入燃灯写章 pipeline
用法: 每章写完 → 自动标注情绪 → 更新曲线 → 检测隐患
"""

from randen.tools.chapter_memory import ChapterMemory
from randen.tools.review_store import ReviewStore
from randen.tools.emotion_annotator import EmotionAnnotator
from randen.tools.emotion_arc_analyzer import EmotionArcAnalyzer
from randen.tools.emotion_visualizer import EmotionVisualizer

class EmotionGuard:
    """燃灯 Studio 情感守卫 — 挂载于每章审查后"""

    def __init__(self, project_path: str):
        self.annotator = EmotionAnnotator(
            f"{project_path}/config/emotion_arc.yaml"
        )
        self.analyzer = EmotionArcAnalyzer(
            f"{project_path}/config/emotion_arc.yaml"
        )
        self.visualizer = EmotionVisualizer(project_path)
        self.memory = ChapterMemory(project_path)
        self.reviews = ReviewStore(project_path)

    def on_chapter_reviewed(self, chapter_id: int, reviewed_text: str,
                            review_notes: dict):
        """
        挂载点: 每章 goethe 审查完成后 → 情绪标注 + 曲线更新
        """

        # 步骤 1: 自动情绪标注
        emotion_annotation = self.annotator.annotate(
            chapter_id=chapter_id,
            chapter_text=reviewed_text,
            review_notes=review_notes
        )

        # 步骤 2: 如果置信度低，标记需人工确认
        if emotion_annotation["confidence"] < 0.7:
            emotion_annotation["needs_manual_review"] = True
            self.reviews.add_manual_todo(
                f"ch_{chapter_id}_emotion_check",
                "情绪标注置信度低，请手动确认强度/类型"
            )

        # 步骤 3: 持久化标注数据
        self._save_emotion_annotation(chapter_id, emotion_annotation)

        # 步骤 4: 实时检测 —— 仅检查本章相关的即时隐患
        recent_chapters = self._load_recent_emotions(n=15)
        immediate_warnings = []

        # 检查情绪透支
        burnout = self.analyzer.check_emotion_burnout(recent_chapters)
        immediate_warnings.extend(burnout)

        # 检查高潮后恢复
        recovery = self.analyzer.check_recovery_after_climax(recent_chapters)
        immediate_warnings.extend(recovery)

        # 步骤 5: 如需干预，在审查报告中追加
        if immediate_warnings:
            self.reviews.append_emotion_warnings(chapter_id, immediate_warnings)

        # 步骤 6: 更新曲线数据（增量）
        self.visualizer.update_curve(chapter_id, emotion_annotation)

        return {
            "annotation": emotion_annotation,
            "warnings": immediate_warnings
        }

    def on_volume_complete(self, vol_id: int):
        """
        挂载点: 每卷写完 → 全面情感分析 + 生成曲线图
        """

        # 步骤 1: 加载本卷全部情绪数据
        vol_chapters = self._load_volume_emotions(vol_id)
        current_vol = self._build_volume_summary(vol_id, vol_chapters)
        previous_vol = self._build_volume_summary(vol_id - 1)

        # 步骤 2: 运行全部检测规则
        full_check = self.analyzer._run_full_checks(
            chapters=vol_chapters,
            current_vol=current_vol,
            previous_vol=previous_vol
        )

        # 步骤 3: 生成卷级情绪曲线 SVG
        curve_svg = self.visualizer.generate_volume_curve(
            vol_id=vol_id,
            chapters=vol_chapters,
            warnings=full_check
        )

        # 步骤 4: 生成人话总结
        human_summary = self._generate_human_summary(full_check, current_vol)

        # 步骤 5: 写入卷审计报告的情感章节
        vol_report = {
            "curve_svg_path": f"data/reports/emotion/vol_{vol_id}_curve.svg",
            "full_check": full_check,
            "human_summary": human_summary
        }

        self.reviews.add_emotion_section_to_audit(vol_id, vol_report)

        return vol_report

    def _generate_human_summary(self, full_check: dict,
                                 current_vol: dict) -> str:
        """生成人话总结 —— 面向作者的友好表达"""

        parts = []

        # 开场定调
        health = full_check["summary"]["overall_health"]
        parts.append(f"### 🎭 第 {current_vol['id']} 卷情感弧线总评\n")
        parts.append(f"{health}\n")

        # 情绪得分
        avg = current_vol["avg_intensity"]
        parts.append(f"本卷平均情绪强度: **{avg:.1f}/10**\n")

        # 亮点
        true_climaxes = [
            ch for ch in current_vol["chapters"]
            if ch["intensity"] >= 8 and not any(
                w["chapter"] == ch["chapter_id"]
                for w in full_check["fake_climax"]
            )
        ]
        if true_climaxes:
            climax_mentions = ", ".join(
                f"第 {c['chapter_id']} 章" for c in true_climaxes
            )
            parts.append(f"🌟 真高潮: {climax_mentions}\n")

        # 问题
        high_warnings = [
            w for checks in full_check.values()
            if isinstance(checks, list)
            for w in checks
            if w.get("severity") == "high"
        ]
        if high_warnings:
            parts.append(f"\n⚠️ **需要注意的问题:**\n")
            for w in high_warnings:
                parts.append(f"- {w['message']}\n")

        # 建议总结
        suggestions = self._distill_suggestions(full_check)
        if suggestions:
            parts.append(f"\n💡 **建议:** {suggestions[0]}\n")

        return "\n".join(parts)
```

### 5.2 在燃灯 Studio 主流程中的挂载位置

```python
class RandenStudio:
    """燃灯 Studio 主流程 — 展示情绪守卫的挂载"""

    def write_chapter_flow(self, chapter_id: int):
        """写章主流程"""

        # ... 原有: 大纲生成 → context构建 → LLM写作 → 审查 ...

        raw = self.generate_chapter(chapter_id)
        reviewed = self.goethe_reviewer.review(raw)

        # === 情绪守卫挂载点: 审查完成后 ===
        emotion_guard = EmotionGuard(self.project_path)
        emotion_result = emotion_guard.on_chapter_reviewed(
            chapter_id=chapter_id,
            reviewed_text=reviewed["final_text"],
            review_notes=reviewed["notes"]
        )

        # 如果情绪标注置信度低 → 提示作者
        if emotion_result["annotation"].get("needs_manual_review"):
            self.ui.show_sidebar_notification(
                "🎭 情绪标注需确认",
                f"第 {chapter_id} 章的情绪标注置信度偏低，请检查。",
                action={"label": "确认标注", "target": f"emotion_review/{chapter_id}"}
            )

        # 如果即时告警 → 在审查面板展示
        if emotion_result["warnings"]:
            for w in emotion_result["warnings"]:
                self.ui.append_review_warning(
                    chapter_id=chapter_id,
                    icon="🎭",
                    message=w["message"],
                    suggestion=w.get("suggestion", "")
                )

        self.save_chapter(chapter_id, reviewed["final_text"])

    def close_volume_flow(self, vol_id: int):
        """封卷流程"""

        # ... 原有: 记忆压缩、真相文件归档、一致性审计 ...

        # === 情绪守卫挂载点: 卷封存时 ===
        emotion_guard = EmotionGuard(self.project_path)
        vol_report = emotion_guard.on_volume_complete(vol_id)

        # 在卷审计报告中追加情感章节
        self.audit_report.append_section(
            vol_id=vol_id,
            section_title="## 🎭 情感弧线分析",
            content=vol_report["human_summary"]
        )

        # 更新全局情感仪表盘
        self.studio_dashboard.refresh_emotion_panel(vol_id)

    def studio_startup(self):
        """燃灯 Studio 启动——初始化仪表盘"""

        # 加载最近卷的情感曲线图
        current_vol = self.project.get_current_volume()
        latest_curve = f"data/reports/emotion/vol_{current_vol}_curve.svg"

        # 在侧边栏展示简化版曲线
        self.ui.sidebar.add_widget("emotion_mini_chart", {
            "title": "情感趋势",
            "chart_path": latest_curve,
            "on_click": "open_emotion_dashboard"
        })
```

### 5.3 CLI 独立命令

```python
# 燃灯 CLI 新增命令
#
# randen emotion annotate ch_0156           → 标注单章情绪
# randen emotion curve vol 3                → 生成卷级情感曲线
# randen emotion check vol 3                → 运行情感结构检测
# randen emotion dashboard                  → 生成全作品情感仪表盘 HTML

# tools/cli.py 扩展:

@cli.group()
def emotion():
    """情感弧线分析与可视化"""
    pass

@emotion.command()
@click.argument("chapter_id")
def annotate(chapter_id: str):
    """标注单章情绪"""
    guard = EmotionGuard(PROJECT_PATH)
    text = load_chapter(chapter_id)
    result = guard.annotator.annotate(
        chapter_id=parse_chapter_id(chapter_id),
        chapter_text=text,
        review_notes={}
    )
    click.echo(f"强度: {result['intensity']}/10  类型: {result['type']}  置信度: {result['confidence']:.0%}")

@emotion.command()
@click.argument("vol_id", type=int)
@click.option("--format", type=click.Choice(["svg", "png", "html"]), default="svg")
def curve(vol_id: int, format: str):
    """生成卷级情感曲线"""
    guard = EmotionGuard(PROJECT_PATH)
    visualizer = EmotionVisualizer(PROJECT_PATH)
    chapters = load_volume_emotions(vol_id)
    path = visualizer.generate_volume_curve(vol_id, chapters, format=format)
    click.echo(f"曲线已生成: {path}")

@emotion.command()
@click.argument("vol_id", type=int)
def check(vol_id: int):
    """全卷情感结构检测"""
    guard = EmotionGuard(PROJECT_PATH)
    report = guard.on_volume_complete(vol_id)
    click.echo(report["human_summary"])

@emotion.command()
@click.option("--output", type=click.Path(), default="data/reports/emotion/dashboard.html")
def dashboard(output: str):
    """生成全作品情感仪表盘"""
    visualizer = EmotionVisualizer(PROJECT_PATH)
    html = visualizer.generate_full_dashboard_html()
    with open(output, "w") as f:
        f.write(html)
    click.echo(f"仪表盘已生成: {output}")
```

---

## 六、实施路线图

### Phase 1: 标注引擎 (v1.0)

- [x] 情绪标注维度设计（本文档定义）
- [ ] 自动标注引擎（基于 LLM 的章节情绪分析 Prompt）
- [ ] 手动标注覆盖界面
- [ ] 标注数据持久化

### Phase 2: 检测规则 (v1.1)

- [ ] 情绪平原检测
- [ ] 假高潮识别
- [ ] 情绪透支检测
- [ ] 卷间对比 + 情绪压抑趋势
- [ ] 情绪类型分配检测

### Phase 3: 可视化 (v1.2)

- [ ] 卷级情感曲线 SVG 生成
- [ ] Studio 情感仪表盘面板
- [ ] 全作品情感仪表盘 HTML
- [ ] 交互功能（悬停详情/区间选择/卷对比）

### Phase 4: 智能进阶 (v2.0)

- [ ] 参考弧线库（经典作品的情感曲线模板）
- [ ] 情感节奏评分（与参考弧线的相似度评估）
- [ ] 读者情绪预测（基于当前章节预测读者看完后的情绪状态）
- [ ] 情绪因果链分析（什么事件触发了情绪变化，是否合理）
- [ ] 自适应阈值（不同小说类型的情感节奏差异）

---

> *"网文不是写给评论家的——是写给读者的心。你不必让每一章都完美，但你必须知道：读者读到这一章的时候，心里是什么感觉。"*
> *—— 燃灯情感设计原则*
