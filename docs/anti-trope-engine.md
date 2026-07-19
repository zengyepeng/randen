# 燃灯 — 反套路引擎

> 设计日期: 2026-07-19 | 目标: 检测"又是这套"的情节模式，主动建议突破 | 优先级: P1

---

## 为什么需要反套路引擎

网络文学读者是最敏感的群体。他们对套路既渴望又厌恶：

```
"我猜到了" → 觉得没水平      ❌ 伤害最大
"果然如此" → 不惊喜          ⚠️ 勉强 OK
"竟然是这样" → 惊喜记忆点     ✅ 最好的体验
```

问题：2000+ 章长篇小说中，套路重复是必然。AI 默认识别的"好故事"往往是训练语料平均值——正好是最常见的套路模板。

**反套路引擎不是禁止套路，而是帮作者知道：** 你用了什么套路、哪些读者已受够了、怎么翻新——并区分"good trope"（读者就想看这个）vs "bad trope"（让人翻白眼）。

---

## 一、套路库

### 套路清单

```yaml
# data/tropes/library.yaml
tropes:

  - id: trope_001
    name: "老爷爷传功"
    recognizers: ["神秘老人传功", "高人相救后消失", "功力无条件赠送"]
    frequency_threshold: { per_volume: 2, per_500chapters: 3 }
    variants:
      - direction: "传功不是礼物是投资 → 功法是枷锁，练到第七层会被夺舍"
      - direction: "不是传功是封印解除 → 力量本就是他自己的"
      - direction: "传功是双向的 → 老人退回凡人境界"
    good: "老人有完整故事线，非用完即弃的工具人"
    bad: "天降老爷爷 → 赠予 → 消失，全程无付出"

  - id: trope_002
    name: "退婚流"
    recognizers: ["被未婚妻退婚", "家族羞辱主角", "发誓逆袭", "中后期打脸"]
    frequency_threshold: { per_novel: 1 }
    variants:
      - direction: "退婚是保护 → 女方家族逼她联姻，她为不拖累主角而退婚"
      - direction: "主角平静接受 → 他本来就不想结这门亲"
      - direction: "被退婚的反而是强者 → 主角真实身份远高于对方"
    good: "退婚作为开场背景矛盾之一，非唯一驱动力"
    bad: "退婚→奇遇→打脸三连击"

  - id: trope_003
    name: "擂台比武打脸"
    recognizers: ["公开擂台", "主角隐藏实力", "对手嚣张", "全场震惊"]
    frequency_threshold: { per_volume: 1, per_200chapters: 2 }
    variants:
      - direction: "主角意外输了 → 不是所有战斗都要赢"
      - direction: "擂台被突发事件打断 → 外敌入侵，擂台突然不重要了"
      - direction: "主角拒绝比试 → 转身离开，比打赢更打脸"
    good: "擂台是大情节的一部分，非为打脸而打脸"
    bad: "挑衅→隐藏实力→爆发→震惊全场 模板全对"

  - id: trope_004
    name: "拍卖会捡漏"
    recognizers: ["别人都没发现的宝物", "主角眼光独到", "低价入手"]
    frequency_threshold: { per_volume: 1 }
    variants:
      - direction: "捡漏的东西有副作用 → 剑里封印老魔头"
      - direction: "主角被反向捡漏 → 别人低价买走了他真正想要的"
      - direction: "拍卖是一场局 → 都是卖家的陷阱"
    good: "捡漏品后续有独特作用，非工具化外挂"
    bad: "买到就是外挂，直接提升战力"

  - id: trope_005
    name: "坠崖不死反得机缘"
    recognizers: ["被击落悬崖", "众人以为死了", "发现遗府/秘籍", "实力大增"]
    frequency_threshold: { per_novel: 2 }
    variants:
      - direction: "获得了机缘但出不去 → 在洞里待了三年，外面翻天覆地"
      - direction: "没得到任何机缘 → 用手挖了三个月岩壁爬回来"
      - direction: "崖是某个大能的安排 → 被选中而非运气"
    good: "坠崖是真正困境，机缘是克服困境的奖励"
    bad: "坠崖→得传承→暴涨→出去打脸"

  - id: trope_006
    name: "秘境/试炼副本"
    recognizers: ["定期开放秘境", "实力限制", "天材地宝", "主角大放异彩"]
    frequency_threshold: { per_300chapters: 1 }
    variants:
      - direction: "秘境是骗局 → 养蛊场，进去的都是饲料"
      - direction: "秘境未成熟提前开启 → 风险远大于收益"
      - direction: "时间流速不同 → 里面一天外面十年"
    good: "秘境有独特规则和故事，非仅升级场景"
    bad: "秘境=地图→打怪→捡宝→升级 线性流程"

  - id: trope_007
    name: "反派死于话多"
    recognizers: ["必胜局面下长篇解说", "解释计划细节", "给了翻盘时间"]
    frequency_threshold: { per_200chapters: 1 }
    variants:
      - direction: "反派话多但主角还是输了 → 解说本身就是心理战"
      - direction: "话少的反派 → 沉默比话多恐怖十倍"
      - direction: "主角话多拖时间 → 在等救援/阵法完成"
    good: "解说服务于人物塑造（自恋/疯狂），非情节需要"
    bad: "纯为留活路而让反派闭嘴就能赢"

  - id: trope_008
    name: "主角光环级救援"
    recognizers: ["濒死时恰好被救", "救者恰好是神秘高手", "救援精确到毫秒"]
    frequency_threshold: { per_volume: 1 }
    variants:
      - direction: "救援带来更大麻烦 → 救他的人正是追杀他的仇家"
      - direction: "救援付出了代价 → 救命恩人重伤/死了"
      - direction: "救援是主角提前布局的 → 智慧不是运气"
    good: "救援有因果逻辑，非纯粹'恰好'"
    bad: "连续 3 次以上恰好救场"

  - id: trope_009
    name: "暴血开挂无代价"
    recognizers: ["打不过→用禁术", "战力暴增翻盘", "事后无严重后遗症"]
    frequency_threshold: { per_200chapters: 1 }
    variants:
      - direction: "用了禁术确实废了 → 未来 100 章在恢复期"
      - direction: "代价不在身体在别处 → 缩短寿命/失去记忆"
      - direction: "不拼命 — 用智慧/设局取胜"
    good: "每次使用有不可逆代价，读者心疼"
    bad: "暴血→翻盘→下章恢复→再来一次"

  - id: trope_010
    name: "日常打脸标准模板"
    recognizers: ["被纨绔挑衅", "看不起主角", "被迫出手碾压", "靠山也被碾压"]
    frequency_threshold: { per_200chapters: 1 }
    variants:
      - direction: "报警/走法律程序 → 不打架比打架更打脸"
      - direction: "被打是真的被打了 → 一个月后带人抄家"
      - direction: "纨绔反成队友 → 家族安排来考验主角的"
    good: "冲突推动人物关系，非纯粹爽"
    bad: "看不起→挑衅→出手→碾压→观众震惊→靠山→碾压"
```

### 频次阈值

```yaml
# data/tropes/frequency.yaml
frequency_limits:
  per_volume:
    "老爷爷传功": 2    "退婚流": 0    "擂台比武打脸": 1
    "拍卖会捡漏": 1    "坠崖不死": 0  "秘境试炼": 1
    "反派话多": 1      "主角救援": 1  "暴血开挂": 1   "日常打脸": 1
  per_1000chapters:
    "擂台比武打脸": 4  "拍卖会捡漏": 2  "秘境试炼": 3  "日常打脸": 3

threshold_response:
  warning (80%): { action: "审查标注", penalty: 0 }
  excess:         { action: "标注+建议变体", penalty: -5 }
  severe (1.5x):  { action: "红色标注+建议重写", penalty: -10 }
```

---

## 二、检测机制

### 三层检测

```
┌────────────────────────────────────────────────┐
│ 写章前检测 (预写): 大纲是否命中套路 → 提前预警   │
│ 写章后检测 (后审): 成文是否落入套路 → 扣分+建议   │
│ 卷级回顾 (回顾): 统计本卷套路频次 → 趋势报告     │
└────────────────────────────────────────────────┘
```

### 写章前检测

```python
class PreWriteDetector:
    def check_outline(self, outline: str) -> list:
        warnings = []
        for trope in self.library:
            hits = sum(1 for p in trope["recognizers"] if self.fuzzy_match(outline, p))
            if hits / len(trope["recognizers"]) >= 0.6:  # 命中
                freq = self.history.get(trope["id"], {}).get("current_volume", 0)
                thr = trope["frequency_threshold"]["per_volume"]
                if freq >= thr:
                    warnings.append({
                        "level": "high",
                        "trope": trope["name"],
                        "message": f"本卷已使用 {freq} 次（阈值 {thr}），建议变体",
                        "variants": trope["variants"]
                    })
        return warnings
```

### 写章后检测

```python
class PostWriteDetector:
    def classify_trope(self, trope: dict, match_score: float) -> str:
        """good tropes（读者期待）vs bad tropes（审美疲劳）"""
        if match_score >= 0.8 and self.has_good_signal(trope):
            return "good"
        return "bad" if match_score >= 0.7 else "neutral"

    def generate_report(self, chapter: str) -> dict:
        result = self.analyze_chapter(chapter)
        report = {"summary": f"检测到 {len(result['tropes'])} 个套路"}
        for t in result["tropes"]:
            entry = {"trope": t["name"], "classification": t["classification"]}
            if t["classification"] == "bad":
                entry["variants"] = self.get_variants(t["id"])
            report["details"].append(entry)
        return report
```

### 卷级回顾

```markdown
# 套路使用回顾 — 第 5 卷 (ch_0201-ch_0287)

| 套路 | 次数 | 阈值 | 状态 |
|------|------|------|------|
| 老爷爷传功 | 2 | 2 | ⚠️ 已达 |
| 擂台比武 | 2 | 1 | 🔴 超出 1 |
| 日常打脸 | 3 | 1 | 🔴 超出 2 |
| 主角救援 | 1 | 1 | ⚠️ 已达 |

趋势: 日常打脸 卷3:0 → 卷4:1 → 卷5:3 🔴 上升趋势

建议:
1. 日常打脸超出阈值 200% → 建议下卷完全避免
2. 擂台比武 → 下卷必须使用不同变体
3. 读者期待分析：本卷的快节奏爽点读者买账，但下卷需要更高质量冲突来平衡
```

---

## 三、读者期待引擎

核心：不是所有套路都 bad——有些套路读者就等着看。

```yaml
reader_expectation:
  good_tropes:     # 读者期待的"好套路"
    - 深度打脸: "主角隐忍 30 章后在大场面真正出手 — 我等这一天等了 30 章了！"
    - 关键救援: "重要羁绊角色在最危急时刻寻踪而来 — 不是巧合"
    - 伏笔回收: "第 10 章的玉佩，第 500 章解开终极谜题 — 原来在那里等着！"
  bad_tropes:      # 审美疲劳
    - 路边打脸: "无铺垫挑衅→碾压" → "让挑衅者有深层动机"
    - 机械救援: "每次都恰好救场" → "让主角靠自己也有活路"
    - 无缝暴血: "自残→翻盘→没事" → "每次都有真实代价"
```

---

## 四、输出格式

### 写章前预警

```markdown
⚠️ **套路预警 — 第 0154 章大纲**
命中: "擂台比武打脸"（特征匹配 5/5）
本卷已出现 2 次（阈值 1 次）

建议变体方向:
  A. 主角意外输了 → 读者想"他怎么翻盘？"比"果然赢了"值钱
  B. 擂台被外敌打断 → 比武突然不重要了
  C. 主角拒绝上擂台 → "你让我比我就比？"
```

### 写章后审稿标注

```markdown
## 反套路审计 — 第 0154 章
| 套路 | 类型 | 影响 |
|------|------|------|
| 擂台比武 | ⚠️ Bad Trope | −5 |
| 日常打脸 | 🔴 Bad Trope | −8 |

建议: 1. 将"隐藏实力→爆发"改为"全力以赴仍陷入苦战"
      2. 围观反应压缩为一句话
      3. 不以"获胜"结尾 → 获胜后另有阴谋
```

### 卷级回顾

```markdown
# 套路密度趋势 — 卷 1-5
        卷1  卷2  卷3  卷4  卷5
日常打脸  ▁    ▂    ▃    ▄    █   🚨
擂台比武  ▁    ▂    ▁    ▂    ▃   ⚠️
坠崖不死  █    ▁    ▁    ▁    ▁   ✅ 建议不再出现
```

---

## 五、YAML 配置

```yaml
# config/anti_trope.yaml
anti_trope:
  enabled: true
  pre_write_check: true
  post_write_check: true
  volume_review: true
  trope_library: "data/tropes/library.yaml"
  match_threshold: 0.6
  reader_expectation:
    enabled: true
    good_weight: 1.5
    bad_weight: -2.0
    neutral_weight: -0.5
```

---

> 反套路引擎不是消灭套路——套路是人类讲故事的底层工具。它是让作者知道：你正在走一条很多人走过的路，这里有岔路，那边风景可能更好。
