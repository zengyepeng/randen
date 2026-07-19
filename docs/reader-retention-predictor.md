# 燃灯 — 读者留存预测器

> 设计日期: 2026-07-19 | 目标: 识别弃书高危点，按章级+卷级双维度生成可操作的留存报告 | 优先级: P0

---

## 问题定义

网文读者的弃书行为有规律。70% 的弃书行为有至少 3 章的可检测预警窗口。

```
弃书时间分布:
  ├─ 前 20 章: "开头没钩子" — 35%
  ├─ 30-50 章: "开始水了" — 25%
  ├─ 高光后 2-5 章: "高潮过了，不想看了" — 20%
  └─ 中后期: "累觉不爱" — 20%
```

大多数作者在评论区看到"弃了"才知道有读者离开——晚了。**本系统目标：在预警窗口内，用人话告诉作者「这里危险」并给出修补建议。**

---

## 一、弃书模式库

```yaml
# data/retention/drop_patterns.yaml
drop_patterns:

  - id: drop_001  # 主线停滞
    rule: "连续 3 章主线无推进 → 弃书风险 +40%"
    gravity: high
    window: 3
    recognizers:
      - "本章情节未改变任何核心冲突状态"
      - "本章无新信息量（世界/角色/伏笔无增量）"
      - "本章可压缩为 1 句话不丢失信息"
    remedy: "下章必须引入一个新矛盾或揭示一个新信息"

  - id: drop_002  # 无动机角色
    rule: "新角色 5 章内未交代动机 → 弃书风险 +25%"
    gravity: medium
    window: 5
    recognizers:
      - "新角色出场 ≥5 章"
      - "未交代角色目标/欲望/恐惧"
      - "角色可被替换为路人而不影响情节"
    remedy: "下一句对话让角色说出 TA 想要什么"

  - id: drop_003  # 高潮后断崖（最常见弃书点，+60%）
    rule: "高潮后 2 章平淡无新钩子 → 弃书风险 +60%"
    gravity: high
    window: 2
    recognizers:
      - "上一章为主剧情高潮（情绪强度 ≥8）"
      - "本章情绪强度骤降 ≥4 分"
      - "本章末无新的悬念种子"
    remedy: "在高潮尾声中埋一个「下一步」的钩子；让胜利带来新麻烦"

  - id: drop_004  # 场景凝固
    rule: "同一场景停留超过 5 章 → 弃书风险 +35%"
    gravity: medium
    window: 5
    recognizers:
      - "场景标签连续 5 章不变"
      - "无新地图/新势力引入"
      - "读者可感知的「地理范围」未扩大"
    remedy: "插入外部事件打破空间封闭感；用 POV 切换跳出当前场景"

  - id: drop_005  # 主角被动失控
    rule: "主角连续 3 章被动挨打无反击 → 弃书风险 +45%"
    gravity: high
    window: 3
    recognizers:
      - "主角未主动做出影响情节的决策"
      - "主角处境比上一章更差且非主观选择"
      - "应对方式与上一章相同（无策略升级）"
    remedy: "下一章必须给主角一个主动行动——哪怕是错误的选择"

  - id: drop_006  # 新卷无锚点
    rule: "新卷开头 3 章无核心冲突预告 → 弃书风险 +30%"
    gravity: medium
    window: 3
    recognizers:
      - "当前为卷首 3 章之内"
      - "读者无法用一句话概括「这卷要讲什么」"
      - "卷首与上卷结尾无因果衔接"
    remedy: "新卷第一章末尾用一句话锚定本卷核心冲突"

  - id: drop_007  # 叙述比例失衡
    rule: "对话/描写比例连续偏离基线 >30% → 弃书风险 +20%"
    gravity: low
    window: 3
    recognizers:
      - "连续 3 章对话占比偏离作者基线 ±30%"
      - "连续 3 章描写占比偏离作者基线 ±30%"
    remedy: "对话过多→插入独白或环境描写；描写过多→插入对话打破画面"

  - id: drop_008  # 信息过载
    rule: "单章新概念 >10 个 或 3 章内新角色 >8 人 → 弃书风险 +25%"
    gravity: medium
    window: 3
    recognizers:
      - "新专有名词首次出现密度 >10 个/章"
      - "新命名角色 3 章内 >8 人"
      - "世界设定段落超过全章 40%"
    remedy: "把设定藏进情节；新角色分批出场，每批给 3 章消化时间"

  - id: drop_009  # 连续无冲突
    rule: "连续 5 章无任何形式冲突 → 弃书风险 +35%"
    gravity: medium
    window: 5
    recognizers:
      - "5 章内无外部冲突/内部冲突/人际冲突"
    remedy: "最小冲突注入：让一个角色对主角说了句不该说的话"

  - id: drop_010  # 回忆堆积
    rule: "情绪上升段插入 >800 字回忆 → 弃书风险 +20%"
    gravity: medium
    window: 1
    recognizers:
      - "当前情节处于情绪上升段"
      - "插入 >800 字回忆/闪回"
      - "回忆与当前冲突关联度 <50%"
    remedy: "回忆压缩到 200 字以内，只讲当前需要的那部分"
```

### 风险等级映射

```yaml
# data/retention/risk_levels.yaml
risk_mapping:
  # 加权求和：∑(命中模式 × gravity权重 × 窗口紧迫度)
  levels:
    safe:       { range: [0, 15],    color: green,  label: "✅ 安全" }
    watch:      { range: [15, 30],   color: yellow, label: "⚠️ 关注" }
    warning:    { range: [30, 50],   color: orange, label: "🔶 预警" }
    dangerous:  { range: [50, 75],   color: red,    label: "🔴 危险" }
    critical:   { range: [75, 100],  color: purple, label: "💀 高危" }

  gravity_weights: { high: 1.0, medium: 0.6, low: 0.3 }
```

---

## 二、检测流程

### 三级检测体系

```
【每章级】每写完一章 → 扫描上一章+当前章 → 生成风险报告 → data/reports/retention/ch_{n}_risk.md
【趋势分析】每 10 章 → 回顾风险分数走势 → 上升/下降/波动/持平 → 识别高复发模式
【卷级回顾】每写完一卷 → 全卷热力图 → 标记 Top 3 危险点 → 跨卷对比
```

### 核心检测伪代码

```python
class RetentionPredictor:

    def __init__(self):
        self.patterns = load_yaml("data/retention/drop_patterns.yaml")
        self.risk_config = load_yaml("data/retention/risk_levels.yaml")
        self.history = load_recent_history(n=30)

    def analyze_chapter(self, ch_id: int, text: str,
                        prev_ch_id: int, prev_text: str) -> dict:
        hits = []
        cumulative_risk = 0.0

        for p in self.patterns:
            # 匹配识别特征 + 回溯历史检测连续命中
            match = self._match(p, text, prev_text, self.history, ch_id)
            if not match["matched"]:
                continue

            gravity = self.risk_config["gravity_weights"][p["gravity"]]
            urgency = min(match["consecutive_hits"] / p["window"], 1.0)
            contribution = gravity * urgency * 100

            cumulative_risk += contribution
            hits.append({
                "pattern": p["name"], "consecutive": match["consecutive_hits"],
                "threshold": p["window"], "contribution": round(contribution, 1),
                "remedies": p["remedy"]
            })

        level = self._classify(cumulative_risk)
        report = self._generate_report(ch_id, cumulative_risk, level, hits)
        self._save(ch_id, report)
        return report

    def _match(self, p, text, prev_text, history, ch_id):
        current_hits = sum(1 for r in p["recognizers"]
                          if self._check(r, text, ch_id))
        hit_ratio = current_hits / len(p["recognizers"])

        # 回溯连续命中
        consecutive = 1
        for past in reversed(history[-p["window"]:]):
            if past.get("matched") and p["id"] in past["matched_patterns"]:
                consecutive += 1
            else:
                break

        return {"matched": hit_ratio >= 0.5 and consecutive >= 1,
                "hit_ratio": hit_ratio, "consecutive_hits": consecutive}
```

### 趋势分析（每 10 章）

```python
class TrendAnalyzer:
    def analyze_trend(self, start_ch: int, end_ch: int) -> dict:
        scores = [r["cumulative_risk"] for r in self._load_range(start_ch, end_ch)]
        slope = linear_regression_slope(scores)
        avg = sum(scores) / len(scores)

        if slope > 2.0:    trend = "🔴 急剧上升"
        elif slope > 0.5:  trend = "🟠 缓慢上升"
        elif slope > -0.5: trend = "🟡 保持平稳"
        elif slope > -2.0: trend = "🟢 缓慢下降"
        else:              trend = "✅ 快速下降"

        return {"trend": trend, "slope": round(slope, 2), "avg": round(avg, 1)}
```

---

## 三、报告格式（人话优先）

### 设计原则

```
✅ "你的主角已经连续 2 章没有主动推动剧情了"         — 具体
❌ "主线推进指数偏低"                               — 抽象
✅ "下章再不给主角一个行动目标，风险将升至 35%"        — 可操作
❌ "请关注主线推进情况"                              — 无方向
✅ "你的读者现在可能已经有点没耐心了"                  — 有温度
❌ "读者留存概率 = 0.68"                             — 机械
```

### 单章报告示例

```markdown
## 📊 弃书风险报告 — 第 0154 章

### 🟢 综合评分: 12% · 安全
本章没问题——主线在推进，节奏健康。

### ⚠️ 需要关注
**主角主动权: 连续 2 章被动**
你的主角已经连续 2 章没有主动推动剧情了。虽然目前风险不高，
但提醒：**下章再不给主角一个行动目标，风险将升至 35%。**

> 💡 让主角在下一章开篇做一个决定——哪怕决定是错的。

### 📈 本卷趋势
0150 ▁▁▁▂▃ 8%    0151 ▁▁▂▃▅ 18%   0152 ▁▂▃▅▆ 26% ← 高潮后回落
0153 ▁▁▁▂▃ 9%   0154 ▁▁▂▃▅ 12%
趋势: 🟢 平稳

### 🎯 预测
第 0157 章正接近「高潮后断崖期」弃书窗口——如果 0156 是高光章节，
注意在 0157 章埋一个「接下来的问题」。
```

### 卷级热力图示例

```markdown
## 📊 弃书风险热力图 — 第 3 卷 (ch_0101 - ch_0180)

### 综合: 18.3% · 安全 (↓ 低于卷2的 22.7%)

### 🔴 整卷最危险的 3 个点

| 章 | 风险 | 原因 | 状态 |
|----|------|------|------|
| 0107 | 42% | 新角色"韩铁山"出场 7 章未交代动机 | ❌ 建议补 |
| 0168 | 38% | 青云宗内 3 章无主线推进 | ❌ 建议补 |
| 0123 | 26% | 高潮后缓冲不足 | ⚠️ 部分修复 |

### 📊 分模式统计

| 模式 | 命中 | 最严重 | 趋势 |
|------|------|--------|------|
| 主线停滞 | 3 | 0168 | 🟠 上升 |
| 高潮后断崖 | 2 | 0123 | 🟡 持平 |
| 无动机角色 | 1 | 0107 | ✅ 已解决 |

### 💬 人话总结
> 第 3 卷整体健康，但有两个隐患：① 第 0107 章的「韩铁山」还是个谜，给他说清楚要什么；
> ② 第 0165-0168 章酝酿 3 章有点长了，0169 章必须炸。
> 好消息：卷末悬念设置漂亮。读者会带着问题进入第 4 卷。
```

---

## 四、「好弃书点」vs「坏弃书点」

```yaml
# data/retention/drop_types.yaml
drop_types:

  good_drop:   # 读者暂时放下书，但一定会回来看
    locations: ["每卷结尾", "大高潮结束并埋下卷钩子", "分册结尾"]
    characteristics:
      - 当前悬念已解决 + 新悬念已种下
      - 读者情感上得到「阶段性满足」
      - 脑中自然产生「接下来会怎样？」
    risk_contribution: -5  # 加分
    example: "卷末主角击败强敌，但废墟中发现书信——帝国真正敌人不是北境，是朝堂。"

  bad_drop:    # 读者放弃不再回来
    locations: ["章中平淡段落", "高潮后无钩子", "信息过载段"]
    characteristics:
      - 无未解决的悬念拉住读者
      - 读者「忘了看到哪了」
      - 重拿起来需回忆大量信息 → 算了吧追新书
    risk_contribution: +30  # 扣分
    example: "第 0238 章：日常逛街+遇路人+路人看不起主角+主角淡定离开。无事发生。"

  neutral_drop:  # 因人而异，不计分
```

**核心规则：** 卷末可以有悬念式弃书点（好弃书点，读者会回来），但章中绝对不行（坏弃书点）。

```python
class DropPointClassifier:
    def classify(self, ch_id: int, text: str, outline: dict) -> dict:
        is_vol_end = outline.get("is_volume_end", False)
        pos = outline.get("chapter_position", "middle")

        if is_vol_end:
            has_hook = self._has_new_hook(text)
            has_resolution = self._has_resolution(text)
            if has_hook and has_resolution:
                return {"type": "good_drop", "msg": "✅ 悬念已收+新钩已放，读者会回来"}
            return {"type": "neutral_drop", "msg": "⚠️ 建议追加新钩子"}

        # 章中 → 绝对不允许坏弃书点
        if pos in ("start", "middle") and self._is_bad_drop(text):
            return {"type": "bad_drop",
                    "msg": "🔴 章中坏弃书点——章中弃书≈大概率不会回来",
                    "risk_contribution": 30}
        return {"type": "neutral_drop"}
```

---

## 五、YAML 配置

```yaml
# config/reader_retention.yaml
reader_retention:
  enabled: true
  pattern_library: "data/retention/drop_patterns.yaml"
  risk_levels: "data/retention/risk_levels.yaml"

  checks:
    per_chapter: true        # 每章写完自动检测
    trend_10ch: true         # 每 10 章趋势分析
    volume_review: true      # 每卷热力图回顾
    predictive_alert: true   # 预测未来 N 章弃书风险

  match:
    recognizer_threshold: 0.5
    window_lookback: 30
    urgency_weight: true

  baseline:
    auto_calibrate: true
    recalibration_interval: 50  # 每 50 章重校准
    metrics: [dialogue_ratio, description_ratio]

  alerts:
    on_warning: "审查标注"
    on_dangerous: "标注+暂停建议"
    on_critical: "暂停+强制回顾"
    notify_channel: "studio"
```

---

## 六、集成示例

### 6.1 在写章流程中挂载

```python
# tools/retention_guard.py

class RetentionGuard:
    def __init__(self, project_path: str):
        self.predictor = RetentionPredictor(f"{project_path}/config/reader_retention.yaml")
        self.trend = TrendAnalyzer()
        self.classifier = DropPointClassifier()
        self.memory = ChapterMemory(project_path)
        self.reviews = ReviewStore(project_path)

    def on_chapter_written(self, ch_id: int, text: str) -> dict:
        # 1. 弃书模式检测
        prev = self.memory.get_chapter(ch_id - 1)
        risk = self.predictor.analyze_chapter(ch_id, text, ch_id - 1, prev)

        # 2. 弃书点分类
        drop = self.classifier.classify(ch_id, text,
                                         self.memory.get_outline(ch_id))

        # 3. 持久化
        self.reviews.add_retention_check(ch_id, {
            "risk": risk, "drop": drop, "ts": datetime.now().isoformat()
        })

        # 4. 趋势分析（每 10 章）
        if ch_id % 10 == 0:
            trend = self.trend.analyze_trend(ch_id - 9, ch_id)
            self.reviews.add_trend_check(ch_id, trend)

        # 5. 响应
        return self._decide(risk, drop)

    def _decide(self, risk, drop) -> dict:
        level = risk["level"]["level"]
        if level in ("dangerous", "critical"):
            return {"action": "block", "msg": f"⚠️ 弃书风险过高({risk['cumulative_risk']:.1f}%)，请修复后再继续"}
        elif level == "warning":
            return {"action": "warn", "msg": risk["summary"], "suggestions": risk["top_remedies"]}
        return {"action": "pass"}

    def on_volume_complete(self, vol_id):
        from randen.tools.retention_volume import VolumeReviewAnalyzer
        vol_report = VolumeReviewAnalyzer().analyze_volume(vol_id,
            self.memory.get_volume_chapter_ids(vol_id))
        self.reviews.add_volume_retention(vol_id, vol_report)
        return vol_report


# ============================================================
# 燃灯 Studio 主流程挂载
# ============================================================

class RandenStudio:
    def write_chapter_flow(self, ch_id: int):
        # ... 大纲生成、上下文构建、LLM写作、审查 ...

        # === 挂载点 1: 写章前预检 ===
        guard = RetentionGuard(self.project_path)
        pre = guard.predictor.pre_write_check(ch_id)
        if pre["risk_prediction"] > 30:
            self.ui.show_warning(pre["message"])

        reviewed = self.review_chapter(self.generate_chapter(ch_id))

        # === 挂载点 2: 写章后检测 ===
        result = guard.on_chapter_written(ch_id, reviewed)
        if result["action"] == "block":
            self.ui.show_blocking_alert(result)
            return None
        elif result["action"] == "warn":
            self.ui.show_warning_banner(result)

        self.save_chapter(ch_id, reviewed)
        return reviewed

    def close_volume_flow(self, vol_id):
        guard = RetentionGuard(self.project_path)
        vol_report = guard.on_volume_complete(vol_id)
        self.append_to_audit(vol_id, "读者留存分析", vol_report)
```

### 6.2 在 Studio UI 中的呈现

```
┌────────────────────────────────────────────────────────────┐
│  燃灯 Studio                                   📊 仪表盘   │
├────────────────────────────────────────────────────────────┤
│  📝 第 0154 章 — 编辑中                                    │
│  ┌─ 留存面板 ──────────────────────────────────────────┐  │
│  │  🟢 弃书风险 12% · 安全                               │  │
│  │  ⚠️ 主角连续 2 章无主动决策                            │  │
│  │     下章必须给行动目标，否则风险升至 35%                │  │
│  │  ┌ 预测 ──────────────────────────────────────┐      │  │
│  │  │ 0155:🟢18% 0156:🟡22% 0157:🟠35%←注意埋钩子 │      │  │
│  │  └───────────────────────────────────────────┘      │  │
│  │  [查看详细报告]  [一键修复建议]                        │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

---

## 七、实施路线图

| 阶段 | 内容 | 状态 |
|------|------|------|
| v1.0 | 模式库 + 单章检测 + 人话报告 | 📝 本文档 |
| v1.1 | 趋势分析 + 预测引擎 + 基线校准 | 📋 待开发 |
| v1.2 | 卷级热力图 + Studio UI 面板 | 📋 待开发 |
| v2.0 | 读者分群 + A/B测试 + 自适应窗口 | 🔮 规划 |

---

> *"读者不会告诉你他们要弃书了——他们只是某一天忘了点开下一章。而你的任务是：让他们绝对舍不得忘记。"*
