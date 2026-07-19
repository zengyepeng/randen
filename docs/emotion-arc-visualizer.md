# 燃灯 — 情感弧线可视化

> 设计日期: 2026-07-19 | 目标: 逐章标注情绪强度与类型，绘制全卷情感曲线，识别情绪结构中的隐患 | 优先级: P0

---

## 问题定义

网文是情感产业。读者追更不是为了看情节——情节是载体，情感才是读者买单的东西。

```
读者的追更心理模型:
  "这一章让我爽了" → 想追下一章
  "最近几章都差不多" → 养着吧
  "我都忘了上次好看是哪章了" → 弃了

核心矛盾: 作者感知不到情感的「边际递减效应」。
         第 50 次爽点和第 1 次给读者的冲击完全不同，
         但作者在写的时候，体验到的疲劳与读者完全不同步。
```

**目标：** 让作者像看股票 K 线图一样，直观看到作品的情感走向——哪里在耗竭读者的情绪资源，哪里给得太少，哪里节奏正要出事。

---

## 一、情绪标注维度

### 1.1 三维标注

```yaml
# 每章情绪标注格式
chapter_emotion:
  chapter_id: 156
  intensity: 7               # 维度 1: 情绪强度 (1-10)
  type: "燃"                 # 维度 2: 情绪类型
  type_secondary: "爽"       # 副类型（混合情绪）
  reader_pulse:              # 维度 3: 心跳曲线
    pre_slope: "steep_rise"  # 高潮前斜率
    post_recovery: "slow"    # 高潮后恢复
    breather_needed: false   # 是否需要喘息章
```

### 1.2 强度标尺 (1-10)

| 分值 | 名称 | 描述 | 读者体验 | 限制 |
|------|------|------|----------|------|
| 1 | 极平静 | 纯粹日常/设定，无冲突 | 养书/准备跳过 | 连续 ≤5 章 |
| 2 | 轻度日常 | 日常中有轻微情绪波动 | 放松但不无聊 | 连续 ≤8 章 |
| 3 | 温和推进 | 有信息量但无紧迫感 | 还行，看看后面 | 连续 ≤10 章 |
| 4 | 小波澜 | 轻微冲突，「有事要发生」 | 有点意思了 | 无限制 |
| 5 | 中等张力 | 冲突升级，读者开始关心 | 想知道接下来 | 无限制 |
| 6 | 紧张 | 明显情绪卷入 | 停不下来 | 连续 ≤6 章 |
| 7 | 激烈 | 情绪近峰值 | 心跳加速 | — |
| 8 | 真高潮 | 卷级/书级重大高潮 | 值得截图发朋友圈 | 每卷 ≥1 次 |
| 9 | 极限情绪 | 燃到流泪/虐到心痛 | 看完会缓很久 | 每卷 ≤2 次 |
| 10 | 神回 | 全书级名场面 | 成为记忆锚点 | 全书 ≤5 次 |

### 1.3 七种情绪类型

```yaml
# data/emotion/emotion_types.yaml
emotion_types:
  - id: "燃"    # 热血: 突破极限/以弱胜强/信念爆发
    intensity_range: [5, 10]
    overuse: "连续燃 = 读者累 → 需要日常缓冲"
    max_ratio: 0.4  # 占全卷比例上限

  - id: "虐"    # 悲痛: 失去/牺牲/背叛/无力感
    intensity_range: [4, 10]
    prerequisite: "必须有充分铺垫，否则虐不动"
    overuse: "连续虐 = 读者跑路 → 虐后必须配甜/燃"
    max_consecutive: 3
    max_ratio: 0.25

  - id: "甜"    # 温馨: 情感升温/默契/守护
    intensity_range: [1, 6]
    best_placement: "虐的后面，或日常间隙中穿插"
    overuse: "纯甜无冲突 = 工业糖精"

  - id: "悬"    # 紧张: 谜团/危机预感/未知恐惧
    intensity_range: [3, 9]
    max_consecutive_without_reveal: 15  # 15 章不揭谜底→警告

  - id: "悲"    # 苍凉: 宏大叙事中的无力感/宿命
    intensity_range: [2, 8]
    best_placement: "卷末/重大转折点"
    overuse: "过度悲凉 = 读者压抑不想读"

  - id: "爽"    # 畅快: 打脸/碾压/收债/压抑后释放
    intensity_range: [4, 9]
    prerequisite: "爽的程度 = 压抑程度 × 释放合理度"

  - id: "日常"  # 过渡: 自然互动/世界细节/轻松段落
    intensity_range: [1, 4]
    function: "情绪缓冲——没有日常就没有高潮"
    note: "日常也需 micro-tension，绝对平静 = 无聊"
```

### 1.4 混合情绪

```yaml
# data/emotion/mixed_emotions.yaml
mixed:
  - pair: ["燃", "悲"] → "壮烈": 胜利中感受代价的沉重——最高级的情绪复合体
  - pair: ["甜", "虐"] → "刀糖": 温馨中埋伏刀子——甜里尝到苦
  - pair: ["爽", "悬"] → "悬爽": 爽了一把但更大的问题随之浮出
  - pair: ["日常", "悲"] → "平淡悲": 日常中透出无力感——比正面写悲更有余韵
```

---

## 二、检测规则

### 2.1 六大结构性隐患

```python
class EmotionArcAnalyzer:

    def __init__(self, config_path: str):
        self.scale = load_yaml("data/emotion/intensity_scale.yaml")
        self.types = load_yaml("data/emotion/emotion_types.yaml")

    # ============ 规则 1: 情绪平原 ============
    def check_plateau(self, chapters: list[dict]) -> list[dict]:
        """
        连续 10 章强度波动 < 2 分 → 危险区间
        原理: 读者的情绪需要有峰有谷。全是一个调 = 催眠。
        """
        warnings = []
        for i in range(len(chapters) - 9):
            window = chapters[i:i+10]
            intensities = [ch["intensity"] for ch in window]
            variance = max(intensities) - min(intensities)

            if variance < 2:
                avg = sum(intensities) / 10
                sev = "high" if avg < 3 else "medium"
                warnings.append({
                    "type": "emotion_plateau", "severity": sev,
                    "range": f"ch_{window[0]['id']}-{window[-1]['id']}",
                    "message": f"连续 10 章波动仅 {variance} 分——读者感觉「一直是这个调」",
                    "suggestion": ("引入意外事件打破平静" if avg < 3
                                   else "插入短暂情绪低谷，让读者重建对波动的敏感度")
                })
        return warnings

    # ============ 规则 2: 假高潮 ============
    def check_fake_climax(self, chapters: list[dict], vol_id: int) -> list[dict]:
        """
        每卷至少 1 次强度 ≥8 的真高潮，不能全用「打斗」凑数
        真高潮 = 情绪有质的突破（关系转折/真相/角色蜕变）
        假高潮 = 只有场面没有实质推进
        """
        warnings = []
        climaxes = [ch for ch in chapters if ch["intensity"] >= 8]

        if not climaxes:
            return [{"type": "missing_climax", "severity": "high",
                     "message": f"第 {vol_id} 卷无任何强度≥8的高潮——读者感到「这卷好像什么都没发生」"}]

        for ch in climaxes:
            if (ch.get("emotion_type") == "燃"
                and not ch.get("has_plot_consequence")
                and not ch.get("has_character_shift")
                and not ch.get("has_revelation")):
                warnings.append({
                    "type": "fake_climax", "severity": "medium",
                    "chapter": ch["id"],
                    "message": f"第 {ch['id']} 章强度 {ch['intensity']} 但仅有战斗——读者打完就忘了",
                    "suggestion": "在战斗中加入不可逆后果：受伤/失去/获得关键信息/关系改变"
                })
        return warnings

    # ============ 规则 3: 情绪透支 ============
    def check_burnout(self, chapters: list[dict]) -> list[dict]:
        """
        连续 3 章强度 ≥8 → 读者会麻木
        原理: 情绪有「不应期」。连续高强度 = 阈值拉高 =
              后面 9 分读者也只感觉 5 分。情绪是珍贵资源。
        """
        warnings = []
        run = 0
        start = None
        for ch in chapters:
            if ch["intensity"] >= 8:
                if start is None: start = ch["id"]
                run += 1
            else:
                if run >= 3:
                    warnings.append({
                        "type": "emotion_burnout", "severity": "high",
                        "range": f"ch_{start}-{ch['id']-1}",
                        "message": f"连续 {run} 章强度≥8——情绪透支，后续高潮失去冲击力",
                        "suggestion": "高强度间必须有 1-2 章强度 3-5 的喘息章"
                    })
                run = 0; start = None

        if run >= 3:  # 边界
            warnings.append({
                "type": "emotion_burnout", "severity": "high",
                "range": f"ch_{start}-{chapters[-1]['id']}",
                "message": f"连续 {run} 章强度≥8——下一章必须降压",
                "suggestion": "立即插入 2 章强度 3-4 的过渡"
            })
        return warnings

    # ============ 规则 4: 卷间压抑趋势 ============
    def check_volume_depression(self, current: dict, prev: dict) -> list[dict]:
        """
        卷 N 整体情绪比卷 1 低 15% → 读者感到「越来越沉闷」
        长篇天然趋势是「越来越沉重」，但需要平衡。
        """
        warnings = []
        vol1_avg = self._get_vol_avg(1)
        delta = (current["avg_intensity"] - vol1_avg) / vol1_avg * 100

        if delta < -15:
            warnings.append({
                "type": "volume_depression", "severity": "high",
                "message": f"本卷平均强度 ({current['avg_intensity']:.1f}) 比卷1 ({vol1_avg:.1f}) 降 {abs(delta):.0f}%——读者可能感到压抑",
                "suggestion": "下卷安排 2-3 个「回到初心」的章节，打破压抑连续感"
            })
        elif delta < -8:
            warnings.append({
                "type": "volume_depression", "severity": "medium",
                "message": f"比卷1下降 {abs(delta):.0f}%——需关注趋势",
                "suggestion": "下卷至少保持当前水平，不要继续降"
            })

        # 与上一卷对比
        prev_delta = (current["avg_intensity"] - prev["avg_intensity"]) / prev["avg_intensity"] * 100
        if prev_delta < -10:
            warnings.append({
                "type": "volume_drop_sharp", "severity": "medium",
                "message": f"比上卷骤降 {abs(prev_delta):.0f}%——请确认是「暴风雨前平静」还是作者倦怠"
            })
        return warnings

    # ============ 规则 5: 情绪类型分配 ============
    def check_type_distribution(self, chapters: list[dict]) -> list[dict]:
        """单一类型 >60% 或 燃>40% 或 虐>25% → 警告"""
        warnings = []
        total = len(chapters)
        counts = {}
        for ch in chapters:
            etype = ch["emotion_type"]
            counts[etype] = counts.get(etype, 0) + 1

        for etype, count in counts.items():
            ratio = count / total
            if ratio > 0.6:
                warnings.append({
                    "type": "emotion_monotony", "severity": "medium",
                    "message": f"「{etype}」占 {ratio:.0%}——单一情绪持续太久读者会腻"
                })
            if etype == "燃" and ratio > 0.4:
                warnings.append({
                    "type": "燃_过度", "severity": "medium",
                    "message": "「燃」超 40%——没有日常缓冲的燃是噪音",
                    "suggestion": "每 2-3 章燃后插入 1 章日常或甜"
                })
            if etype == "虐" and ratio > 0.25:
                warnings.append({
                    "type": "虐_过度", "severity": "high",
                    "message": "「虐」超 25%——读者需要看到希望",
                    "suggestion": "安排 2-3 章甜或爽来修复读者情绪"
                })
        return warnings

    # ============ 规则 6: 高潮后恢复 ============
    def check_recovery(self, chapters: list[dict]) -> list[dict]:
        """高潮后是否有足够缓冲"""
        warnings = []
        for i, ch in enumerate(chapters):
            if ch["intensity"] >= 8 and i < len(chapters) - 1:
                nxt = chapters[i+1]
                if nxt["intensity"] >= 7:
                    warnings.append({
                        "type": "no_recovery", "severity": "medium",
                        "chapter": nxt["id"],
                        "message": f"高潮后下一章强度仍为 {nxt['intensity']}——读者没时间消化",
                        "suggestion": "高潮后至少给 1 章强度 3-5 的恢复期"
                    })
                elif nxt["intensity"] <= ch["intensity"] - 6:
                    warnings.append({
                        "type": "sharp_drop", "severity": "low",
                        "chapter": nxt["id"],
                        "message": f"高潮后强度骤降 {ch['intensity']}→{nxt['intensity']}——落差太大",
                        "suggestion": "在骤降中保留一个小悬念/新线索"
                    })
        return warnings
```

### 2.2 全面检查汇总

```python
class EmotionArcFullCheck:
    def run_all(self, chapters, current_vol, previous_vol) -> dict:
        a = EmotionArcAnalyzer()
        results = {
            "plateau": a.check_plateau(chapters),
            "fake_climax": a.check_fake_climax(chapters, current_vol["id"]),
            "burnout": a.check_burnout(chapters),
            "depression": a.check_volume_depression(current_vol, previous_vol),
            "types": a.check_type_distribution(chapters),
            "recovery": a.check_recovery(chapters),
        }

        sev = {"high": 0, "medium": 0, "low": 0}
        for checks in results.values():
            for w in checks:
                sev[w["severity"]] += 1

        if sev["high"] >= 2:    health = "🔴 严重隐患，建议修复后再继续"
        elif sev["high"] >= 1 or sev["medium"] >= 3: health = "🟠 存在需要关注的问题"
        elif sev["medium"] >= 1 or sev["low"] >= 3:   health = "🟡 总体健康，有小瑕疵"
        else:                                         health = "✅ 情绪结构健康"

        return {"checks": results, "severity": sev, "health": health}
```

---

## 三、情感仪表盘 — Studio 面板设计

### 3.1 面板布局

```
┌────────────────────────────────────────────────────────────┐
│  燃灯 Studio — 🎭 情感仪表盘                      第 3 卷  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─ 全卷情绪曲线 —─────────────────────────────────────┐  │
│  │                                                      │  │
│  │  10 ┤                                        ●        │  │
│  │     │            ●──●                  ●──┘          │  │
│  │   8 ┤       ●──┘    ●──●      ●───┘                 │  │
│  │     │  ●──┘                 ●──┘                    │  │
│  │   6 ┤ ●┘                                              │  │
│  │     │●                  ●─●                           │  │
│  │   4 ┤──●──●──●      ●─●   ●─●                       │  │
│  │     │        ●──●──┘       └─●──●                   │  │
│  │   2 ┤                                                  │  │
│  │   0 ┼────┬────┬────┬────┬────┬────┬────              │  │
│  │      0101  0120  0140  0160  0180                     │  │
│  │                                                      │  │
│  │  标注: ●高潮  ○低谷  ◇转折  ~日常  ⚡假高潮          │  │
│  │  🔴 ch_0112 假高潮 (强度8、仅有战斗、无情节突破)       │  │
│  │  🟢 ch_0145 真高潮 (强度9、伏笔回收+角色蜕变)         │  │
│  │  ⚠️  ch_0160-0170 情绪平原 (10章波动<1.5)             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─ 情绪类型分布 ────────┐ ┌─ 跨卷对比 ──────────────┐   │
│  │ 燃 ████████████ 38%   │ │ 卷1 ████████▌ 6.1        │   │
│  │ 虐 ████ 13%           │ │ 卷2 ███████▌  5.7        │   │
│  │ 甜 ███ 9%             │ │ 卷3 ██████▌   5.2 ⚠️     │   │
│  │ 悬 █████ 15%          │ │ ↓ -14% vs 卷1            │   │
│  │ 爽 ████ 12%           │ └──────────────────────────┘   │
│  │ 日常 ████ 13%         │                                │
│  └────────────────────────┘                               │
│                                                            │
│  ┌─ 人话总结 ──────────────────────────────────────────┐  │
│  │ 💬 "你的读者现在可能有点累了。第 3 卷从 165 章开始     │  │
│  │     持续走低，10 章没有像样的情绪起伏。                 │  │
│  │     好消息：第 145 章的真高潮质量很高——读者会记住。     │  │
│  │     建议下章来点爽的，让读者痛快一把。"                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  [展开曲线详情]  [导出报告]  [AI 优化建议]                  │
└────────────────────────────────────────────────────────────┘
```

### 3.2 交互能力

```yaml
dashboard_interactions:
  hover_detail: "悬停任意点→弹出该章情绪卡片（强度/类型/摘要/关键事件）"
  range_select: "拖拽选择区间→显示统计（平均强度/波动/主要类型/隐患）"
  compare_volumes: "选择两卷→并排对比曲线，高亮差异区域"
  prediction_forward: "基于趋势→预测未来 10 章情绪走向，标注高危区"
  annotation_mode: "作者手动标注特殊意图的章节，跳过自动告警"
  chapter_link: "点击数据点→跳转对应章节编辑界面"
```

---

## 四、YAML 配置

```yaml
# config/emotion_arc.yaml
emotion_arc:
  enabled: true
  auto_annotate: true               # 每章写完自动标注
  manual_override: true             # 允许作者手动修正
  confidence_threshold: 0.7         # 自动标注置信度阈值

  checks:
    emotion_plateau:
      enabled: true
      window: 10                    # 检测窗口（章）
      variance_threshold: 2         # 波动阈值（分）
    fake_climax:
      enabled: true
      intensity_threshold: 8
      plot_consequence_required: true
    emotion_burnout:
      enabled: true
      consecutive_threshold: 3
      intensity_threshold: 8
    volume_depression:
      enabled: true
      delta_percent: 15             # 相比卷1的下降阈值
    type_distribution:
      enabled: true
      single_type_max: 0.6
      燃_max: 0.4
      虐_max: 0.25
    recovery_after_climax:
      enabled: true
      post_climax_max_intensity: 6

  visualization:
    chart:
      type: "line"
      color_by: "type"              # 按类型着色
      annotations: ["高潮", "低谷", "转折", "日常", "假高潮"]
      show_trend_line: true
      interactive: true
    export:
      formats: ["svg", "png", "html"]
      include_data_table: true

  storage:
    directory: "data/emotion/"
    per_chapter: "data/emotion/chapters/ch_{id}_emotion.yaml"
    per_volume: "data/emotion/volumes/vol_{id}_emotion.yaml"
```

---

## 五、集成示例

### 5.1 在写章流程中挂载

```python
# tools/emotion_guard.py

class EmotionGuard:
    """燃灯情感守卫——挂载于每章审查后"""

    def __init__(self, project_path: str):
        self.annotator = EmotionAnnotator(f"{project_path}/config/emotion_arc.yaml")
        self.analyzer = EmotionArcAnalyzer(f"{project_path}/config/emotion_arc.yaml")
        self.visualizer = EmotionVisualizer(project_path)
        self.reviews = ReviewStore(project_path)

    def on_chapter_reviewed(self, ch_id: int, text: str,
                            review_notes: dict) -> dict:
        # 1. 自动情绪标注
        annotation = self.annotator.annotate(ch_id, text, review_notes)

        if annotation["confidence"] < 0.7:
            annotation["needs_manual_review"] = True
            self.reviews.add_manual_todo(
                f"ch_{ch_id}_emotion_check", "情绪标注置信度低，请手动确认"
            )

        # 2. 持久化
        self._save_annotation(ch_id, annotation)

        # 3. 即时检测（仅本章相关）
        recent = self._load_recent_emotions(n=15)
        warnings = []
        warnings.extend(self.analyzer.check_burnout(recent))
        warnings.extend(self.analyzer.check_recovery(recent))

        if warnings:
            self.reviews.append_emotion_warnings(ch_id, warnings)

        # 4. 更新曲线
        self.visualizer.update_curve(ch_id, annotation)

        return {"annotation": annotation, "warnings": warnings}

    def on_volume_complete(self, vol_id: int) -> dict:
        # 加载全卷情绪数据
        chapters = self._load_volume_emotions(vol_id)
        current = self._build_vol_summary(vol_id, chapters)
        previous = self._build_vol_summary(vol_id - 1)

        # 运行全面检测
        full = EmotionArcFullCheck().run_all(chapters, current, previous)

        # 生成曲线 + 人话总结
        curve_path = self.visualizer.generate_volume_curve(vol_id, chapters, full)
        summary = self._gen_human_summary(full, current)

        vol_report = {
            "curve_svg": curve_path,
            "checks": full,
            "summary": summary
        }
        self.reviews.add_emotion_to_audit(vol_id, vol_report)
        return vol_report

    def _gen_human_summary(self, full, current) -> str:
        health = full["health"]
        avg = current["avg_intensity"]

        lines = [
            f"## 🎭 情感弧线总评\n{health}\n",
            f"本卷平均情绪强度: **{avg:.1f}/10**\n"
        ]

        # 收集高危问题
        high = [w for checks in full["checks"].values()
                for w in checks if w.get("severity") == "high"]
        if high:
            lines.append("\n⚠️ **需要注意:**")
            for w in high:
                lines.append(f"- {w['message']}")

        # 提炼建议
        suggestions = [w.get("suggestion") for checks in full["checks"].values()
                       for w in checks if w.get("suggestion")]
        if suggestions:
            lines.append(f"\n💡 **建议:** {suggestions[0]}")

        return "\n".join(lines)


# ============================================================
# 燃灯 Studio 主流程挂载
# ============================================================

class RandenStudio:
    def write_chapter_flow(self, ch_id: int):
        # ... 原有: 大纲→上下文→LLM→审查 ...

        reviewed = self.goethe_reviewer.review(self.generate_chapter(ch_id))

        # === 挂载点: 审查完成后 ===
        emotion = EmotionGuard(self.project_path)
        result = emotion.on_chapter_reviewed(
            ch_id, reviewed["final_text"], reviewed["notes"]
        )

        if result["annotation"].get("needs_manual_review"):
            self.ui.show_sidebar("🎭 情绪标注需确认",
                f"第 {ch_id} 章标注置信度偏低",
                action={"label": "确认", "target": f"emotion/{ch_id}"})

        for w in result["warnings"]:
            self.ui.append_review_warning(ch_id, "🎭",
                w["message"], w.get("suggestion", ""))

        self.save_chapter(ch_id, reviewed["final_text"])

    def close_volume_flow(self, vol_id):
        # ... 原有: 记忆压缩、归档 ...

        emotion = EmotionGuard(self.project_path)
        vol_report = emotion.on_volume_complete(vol_id)

        self.audit.append_section(vol_id,
            "## 🎭 情感弧线分析",
            vol_report["summary"])

        self.studio_dashboard.refresh_emotion_panel(vol_id)

    def studio_startup(self):
        current_vol = self.project.get_current_volume()
        curve = f"data/reports/emotion/vol_{current_vol}_curve.svg"
        self.ui.sidebar.add_widget("emotion_mini", {
            "title": "情感趋势", "chart": curve,
            "on_click": "open_emotion_dashboard"
        })
```

### 5.2 CLI 命令

```python
# randen emotion annotate ch_0156     → 标注单章情绪
# randen emotion curve vol 3          → 生成卷级曲线
# randen emotion check vol 3          → 全卷检测
# randen emotion dashboard            → 生成全作品仪表盘 HTML

@cli.group()
def emotion():
    """情感弧线分析与可视化"""
    pass

@emotion.command()
@click.argument("ch_id")
def annotate(ch_id: str):
    g = EmotionGuard(PROJECT_PATH)
    r = g.annotator.annotate(parse_id(ch_id), load_chapter(ch_id), {})
    click.echo(f"{r['intensity']}/10 {r['type']} 置信度:{r['confidence']:.0%}")

@emotion.command()
@click.argument("vol_id", type=int)
@click.option("--format", type=click.Choice(["svg","png","html"]), default="svg")
def curve(vol_id, format):
    g = EmotionGuard(PROJECT_PATH)
    path = EmotionVisualizer(PROJECT_PATH).generate_volume_curve(
        vol_id, load_vol_emotions(vol_id), format=format)
    click.echo(f"曲线已生成: {path}")

@emotion.command()
@click.argument("vol_id", type=int)
def check(vol_id):
    g = EmotionGuard(PROJECT_PATH)
    click.echo(g.on_volume_complete(vol_id)["summary"])
```

---

## 六、实施路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| v1.0 | 标注引擎（自动+手动） + 数据持久化 | 📝 本文档 |
| v1.1 | 六大检测规则 + 人话总结生成 | 📋 待开发 |
| v1.2 | 卷级曲线生成 + Studio 面板 + 卷对比 | 📋 待开发 |
| v2.0 | 参考弧线库 + 情绪预测 + 因果链分析 + 自适应阈值 | 🔮 规划 |

---

> *"网文不是写给评论家的——是写给读者的心。你不必让每一章都完美，但你必须知道：读者读到这一章的时候，心里是什么感觉。"*
