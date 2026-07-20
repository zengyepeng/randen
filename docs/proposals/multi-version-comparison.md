# 燃灯 — 多版本对比系统

> 设计日期: 2026-07-19 | 目标: 同一章生成 3 个不同走向的版本供作者选择/融合 | 优先级: P2

---

## 为什么需要多版本对比

AI 写作最大的问题不是"写不出来"，而是"一个答案"。模型第一轮输出定调了整章走向，作者永远不知道另一条岔路的故事是什么样。

```
传统流程: 大纲 → 写一章 → 审稿 → 修改 → 下一章
多版本流程: 大纲 → 写三版 A/B/C → 对比面板 → 选/融合 → 下一章
```

核心价值：打破 AI 的"首因效应"（第一版往往最平均但未必最好看），释放作者真正的选择权，并通过选择学习作者偏好。

---

## 一、三个版本的定义

```yaml
# config/multi_version.yaml
versions:
  
  version_a:
    label: "A 版 — 准确执行"
    tagline: "最安全的版本"
    constraints:
      outline_adherence: "strict"     # 100% 按大纲
      creative_freedom: "low"
      narrative_mode: "当前卷默认"
      token_cost: 1.0x
    when_to_use:
      - "日常/过渡章节"
      - "信息释出章节"
      - "作者明确说按大纲走"

  version_b:
    label: "B 版 — 创造性偏移"
    tagline: "安全的惊喜"
    constraints:
      outline_adherence: "moderate"   # 核心事件不变，顺序/角度可变
      creative_freedom: "medium"
      narrative_mode: "当前卷 + 偏移"
      token_cost: 1.2x
    variants_available:
      - "主角视角 → 旁观者视角"
      - "线性叙事 → 倒叙插叙"
      - "压抑基调 → 黑色幽默基调"
      - "长段落 → 短切镜头"
    when_to_use:
      - "常规章节想试试不同味道"
      - "作者对当前风格有疲劳感"
      - "想看看同一情节还能怎么讲"

  version_c:
    label: "C 版 — 自由发挥"
    tagline: "意外之喜"
    constraints:
      outline_adherence: "loose"      # 只保留核心设定+章节目标
      creative_freedom: "high"
      narrative_mode: "自由"
      token_cost: 1.5-2.0x
    when_to_use:
      - "关键转折章（让惊喜概率最大化）"
      - "首章（好的开局比什么都重要）"
      - "卷末高潮章（给读者最极致体验）"
      - "作者创意枯竭时"
```

### 同一场景的三种写法示例

```
【场景】林月回到空无一人的宗门，发现师父留下的信

A 版 — 准确执行:
  林月推开门。殿内空无一人。
  案上放着一封信，是师父的字迹。
  她拆开信，逐字读完——师父说自己去北境了，让她守好宗门。
  她合上信，望着空荡荡的大殿，心中百感交集。

B 版 — 创造性偏移:
  殿里没人。案上那封信立得很正——师父从来不把东西摆这么整齐。
  林月没急着拆信。她把剑卸下，先给自己倒了杯冷茶，喝了，才拿起那封信。
  信上只有四个字：等我回来。她看了很久。然后笑了。

C 版 — 自由发挥:
  大殿只剩下回声。林月在门口站了一炷香——确定真的只有她一个人了。
  桌上没有信。剑也没有。师父带走了那把十七年没离过宗门的旧剑。
  林月蹲下来，把手掌贴在师父常坐的椅子扶手上。木头是凉的。
  "下次偷偷走也记得把信藏好一点啊，师父。"
  她的声音在大殿里撞了一下，没有人接。
```

---

## 二、对比面板

作者看到同一场景的三种写法并列，而非三篇全文。

```markdown
# 第 0154 章 — 多版本对比

| 时段/维度 | A 版 (准确执行) | B 版 (创造性偏移) | C 版 (自由发挥) |
|-----------|----------------|------------------|----------------|
| 开局 | 推门→空无一人 | 注意到信放太整齐 | 站了一炷香 |
| 找信 | 拆信→逐字读完 | 不急着看，先倒茶 | 没有信→师父带走了剑 |
| 反应 | 百感交集，合上信 | 笑了（藏住担心） | 蹲下摸椅子扶手 |
| 金句 | — | "信上只有四个字：等我回来" | "下次偷偷走也记得把信藏好" |
| 节奏 | 线性叙事 🏃 | 慢—顿—快 🎯 | 静—静—物是人非 💔 |
| 情绪 | 淡淡失落 😶 | 克制的不安 🙂 | 失去的实感 😔 |

推荐组合: B 版开局 → C 版中段反应 → A 版结尾 + C 版台词结句
```

### 对比面板数据结构

```yaml
comparison_panel:
  chapter_id: "ch_0154"
  versions:
    a:
      stats:
        word_count: 3540
        sentiment: "neutral_sad"
        golden_lines: 0
        pacing_type: "linear_steady"
        opening_type: "scene_entry"
        closing_type: "emotional_resonance"
    b:
      stats:
        word_count: 3280
        sentiment: "restrained_anxiety"
        golden_lines: 1
        pacing_type: "jazz_syncopation"
        opening_type: "detail_noticing"
        closing_type: "contrast_hook"
    c:
      stats:
        word_count: 3610
        sentiment: "loss_tangibility"
        golden_lines: 2
        pacing_type: "slow_burn"
        opening_type: "still_frame"
        closing_type: "emptiness_echo"
```

---

## 三、选择与融合

### 三种选择方案

```
方案 1 - 单选: 选一个版本作为正文，其他存档
方案 2 - 拼接: "A版开头 + C版对话 + B版结尾"
方案 3 - 融合: 选基准版本，从其他版本"借"句子/意象/节奏
```

### 融合引擎

```python
class VersionMerger:
    def merge_author_selection(self, plan: dict) -> str:
        """
        plan = {
          "base": "b",
          "replacements": {
            "opening": {"source": "a", "paragraphs": [1,2,3]},
            "golden_lines": [{"source": "c", "line": "下次偷偷走也记得..."}],
            "closing": {"source": "a", "from_last": 50}
          }
        }
        """
        merged = self.versions[plan["base"]]
        for key, rep in plan.get("replacements", {}).items():
            src = self.versions[rep["source"]]
            if "paragraphs" in rep:
                merged = self._replace_paragraphs(merged, src, rep["paragraphs"])
            if "from_last" in rep:
                merged = self._replace_closing(merged, src, rep["from_last"])
        return self._polish(merged)  # 润色衔接自然

    def _polish(self, text: str) -> str:
        checks = [self._check_transitions, self._check_pronouns,
                  self._check_voice, self._check_timeline]
        for check in checks:
            for issue in check(text):
                if issue["auto_fixable"]:
                    text = text.replace(issue["text"], issue["fix"])
        return text
```

---

## 四、成本控制

三版本生成的 token 消耗是单版本的 3-4 倍，需智能取舍。

```yaml
# config/version_cost.yaml
chapter_types:
  critical:                         # 必出三版
    types: ["首章", "卷末高潮", "关键转折", "全书高潮"]
    versions: ["a","b","c"]
    cost: "unlimited"
  important:                        # 建议出 A+B
    types: ["关键战斗", "重要人物出场/死亡", "重大揭露", "作者要求"]
    versions: ["a","b"]
    cost: "moderate"
  regular:                          # 默认 A-only
    types: ["过渡", "信息释出", "日常", "修炼准备"]
    versions: ["a"]
    cost: "minimal"
  test:                             # 5% 概率抽中做 B 版对比
    probability: 0.05
    purpose: "采集偏好数据，测试常规章节是否有惊喜需求"
```

### 高峰时段策略

```python
class PeakCostStrategy:
    peak_hours = [9, 10, 11, 14, 15, 16, 17]

    def adjust(self, chapter_type: str, plan: list) -> list:
        if self.is_peak() and chapter_type == "important":
            return ["a"]  # 高峰时段重要章节降为 A-only
        return plan

    def is_peak(self) -> bool:
        from datetime import datetime
        return datetime.now().hour in self.peak_hours
```

---

## 五、版本学习

AI 从作者每次的选择中学习 → 后续即使单版本也更靠近作者口味。

### 学习数据

```yaml
# data/version_learning/preferences.yaml
preference_log:
  ch_0010: { selected: "b", merged_from: { "a": ["opening_3"], "c": ["closing"] }, notes: "B版叙事距离更舒服" }
  ch_0011: { selected: "a", notes: "信息章，A版条理清晰" }
  ch_0015: { selected: "c", notes: "C版方向完全没想到但很喜欢，以后多试试" }

learned_preferences:
  narrative_distance:   { preference: "中距离观察", confidence: 0.65 }
  opening_style:       { preference: "slow_entry",  confidence: 0.70 }
  closing_style:       { preference: "emptiness_echo", confidence: 0.55 }
  frequent_elements:   ["克制的情感表达", "用动作代替心理描写", "短段落切换节奏"]
  rare_elements:       ["长篇内心独白", "形容词堆砌", "叙述者评论"]
```

### 偏好注入

```python
class PreferenceInjector:
    def build_overrides(self) -> dict:
        """返回注入 canonical packet 的风格覆盖"""
        return {
            "narrative_distance": self.preferences.get("narrative_distance", {}).get("preference"),
            "preferred_opening": self.preferences.get("opening_style", {}).get("preference"),
            "preferred_closing": self.preferences.get("closing_style", {}).get("preference"),
            "frequent_elements": self.preferences.get("frequent_elements", []),
            "rare_elements": self.preferences.get("rare_elements", []),
        }

    def get_version_weights(self) -> dict:
        """根据历史选择调整版本概率"""
        weights = {"a": 0.5, "b": 0.35, "c": 0.15}
        counts = {"a": 0, "b": 0, "c": 0}
        total = 0
        for ch, entry in filter_versions(self.log):
            counts[entry["selected"]] += 1; total += 1
        if total >= 5:
            for v in weights: weights[v] = counts[v] / total
        return weights
```

---

## 六、YAML 配置

```yaml
# config/multi_version.yaml
multi_version:
  enabled: true
  versions:
    a: { label: "准确执行",     outline_adherence: "strict",   creative_freedom: "low" }
    b: { label: "创造性偏移",   outline_adherence: "moderate", creative_freedom: "medium" }
    c: { label: "自由发挥",     outline_adherence: "loose",    creative_freedom: "high" }
  chapter_version_map:
    critical: ["a","b","c"]
    important: ["a","b"]
    regular: ["a"]
    test: ["a"]
  cost_control:
    enabled: true
    daily_token_budget: 200000
    peak_hour_reduction: true
    peak_hours: [9,10,11,14,15,16,17]
  preference_learning:
    enabled: true
    min_samples: 5
    update_frequency: "every_10_chapters"
```

---

> 多版本的核心哲学：作者不需要在黑暗中摸索"最好"的那条路——他们只需要在 AI 打开的几扇门里，选最吸引自己的那扇走进去。
