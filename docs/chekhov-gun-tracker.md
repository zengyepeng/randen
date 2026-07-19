# 燃灯 — 契诃夫之枪追踪器

> 设计日期: 2026-07-19 | 目标: 自动检测被"提起但未回收"的物品/信息/特征 | 优先级: P1

---

## 问题定义

契诃夫说：第一幕墙上挂着一把枪，最后一幕前它必须开火。

两千章小说中，墙上挂了 200 把枪——很多"伏笔"其实不是伏笔，而是作者写了就忘的细节。读者记得。到第 800 章还不见下文，信任就磨损一点。

**与 foreshadowing DAG 的区别：**
- DAG：作者已知的伏笔登记 → 跟踪回收状态（管"有意的埋线"）
- 枪追踪器：NLP 自动检测 → 标记跟踪（管"无意的细节"）

---

## 一、检测范围与管道

### 1.1 五类检测目标

```yaml
# config/chekhov-gun-tracker.yaml
detection_scope:
  significant_objects:
    # 被特殊描写（>3句）的物品
    triggers: ["物品+闪光/裂纹/来历不明", "角色反复注视"]
    examples: ["林月的玉佩会发光", "地宫青铜镜的裂纹"]
    priority: high
  significant_information:
    # 被强调但未展开的知识
    triggers: ["'这事以后再说'", "旁白'还不知道'", "传说碎片"]
    examples: ["血月预言", "顾恒师父的遗言"]
    priority: medium
  character_features:
    # 被描写但未参与剧情的特征
    triggers: ["胎记/纹身/伤痕", "来历不明的器物"]
    examples: ["赵墨掌心的火焰胎记", "苏晴失忆前的身份"]
    priority: high
  environmental_anomalies:
    triggers: ["反常自然现象", "地图不存在的地方"]
    examples: ["时间流速异常的古战场"]
    priority: low
  unfinished_business:
    triggers: ["'有机会再去'", "未完的承诺"]
    examples: ["顾恒要找的失传功法"]
    priority: medium
```

### 1.2 检测引擎

```python
# chekhov_gun_detector.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re

@dataclass
class ChekhovGun:
    id: str
    title: str
    category: str
    first_mentioned: int
    last_mentioned: int
    mention_count: int
    mention_chapters: List[int]
    significance_score: float
    status: str = "tracking"   # tracking | stale | expired | resolved

class GunDetector:
    def __init__(self):
        self.guns: Dict[str, ChekhovGun] = {}
        self.counter = 0
    
    def scan_chapter(self, text: str, ch: int):
        # 检测物品（被描述的名词 + 特殊修饰）
        for m in re.finditer(r'(?:那[面把个枚块张件只]?[的]?)?([^{{}}、。，,\n]{2,8})，[^。]{5,40}?(?:来历不明|诡异|发光|裂纹|不寻常)', text):
            name = m.group(1).strip()
            if len(name) >= 2:
                existing = self._find_similar(name)
                if not existing:
                    self.guns[f"g{self.counter:04d}"] = ChekhovGun(
                        id=f"g{self.counter:04d}", title=name,
                        category="object", first_mentioned=ch,
                        last_mentioned=ch, mention_count=1,
                        mention_chapters=[ch], significance_score=self._score(name)
                    )
                    self.counter += 1
        
        # 检测关键信息
        for m in re.finditer(r'(?:这事|此事|真相).{0,10}(?:以后|改天).{0,5}(?:再说|解释)', text):
            info = m.group(0)[:40]
            if not self._find_similar(info):
                self.guns[f"g{self.counter:04d}"] = ChekhovGun(
                    id=f"g{self.counter:04d}", title=info[:20],
                    category="info", first_mentioned=ch, last_mentioned=ch,
                    mention_count=1, mention_chapters=[ch], significance_score=0.7
                )
                self.counter += 1
    
    def _find_similar(self, text: str) -> Optional[ChekhovGun]:
        for g in self.guns.values():
            if len(set(text) & set(g.title)) > len(text) * 0.4:
                return g
        return None
    
    def _score(self, name: str) -> float:
        high = ['神','帝','龙','祖','天','造化','混沌','上古','禁','秘']
        return min(1.0, 0.5 + sum(0.1 for w in high if w in name))
```

---

## 二、生命周期

```
born → tracking → [200章未提 → stale] → [500章未提 → expired]
                → [剧情回收 → resolved]
                → [作者确认忽略 → archived]
```

```yaml
lifecycle:
  stale_threshold: 200
  expired_threshold: 500
  auto_resolve:
    enabled: true
    min_confidence: 0.85  # 低于此需人工确认
  stale_message: "第 {first} 章提到「{title}」，距今 {gap} 章未再出现。是否还有后续计划？"
  expired_message: "第 {first} 章提到「{title}」，距今 {gap} 章未回收。是伏笔还是忘了？"
```

---

## 三、输出格式

```markdown
# 契诃夫之枪追踪报告 — 卷 5
追踪: 47 把枪 | 有效: 12 | 待回收: 21 | 过期: 14

## 🔴 过期警告（>500 章未提及）

### g003 — 林月的玉佩会发光
- 第 87 章首次出现，最近提及第 187 章，已 800 章未解释
- 提及次数: 8 次 | 重要性: ⭐⭐⭐⭐⭐
- **是伏笔还是忘了？**
  - 伏笔 → 登记到 foreshadowing DAG
  - 忘了 → 安排揭示，或删除相关描写
  - 世界观设定 → 在 truth/world_rules.md 补充说明

## 🟡 待回收（200-500 章）

| 编号 | 首次 | 距今 | 标题 |
|------|------|------|------|
| g034 | 第340章 | 235章 | 北境迷雾森林 |

### g034 — 北境迷雾森林
第 340 章作为试炼地点引入，第 450 章说"等时机成熟"→现已第 685 章。
如果不准备写，建议减少对其神秘感的渲染。

## ✅ 已回收（卷5内）
| 编号 | 首次 | 回收 | 标题 | 摘要 |
|------|------|------|------|------|
| g001 | 第5章 | 第420章 | 林月的身份玉牌 | 帝国遗孤信物 |
```

---

## 四、集成方案

```yaml
# config/chekhov-gun-tracker.yaml
enabled: true
run_on: post_10_chapters
detection_scope:
  significant_objects: { enabled: true, priority: high }
  significant_information: { enabled: true, priority: medium }
  character_features: { enabled: true, priority: high }
  environmental_anomalies: { enabled: false, priority: low }
  unfinished_business: { enabled: true, priority: medium }
lifecycle:
  stale_threshold: 200
  expired_threshold: 500
  require_ack: true
  auto_resolve: { enabled: true, min_confidence: 0.85 }
output:
  report_path: data/chekhov-guns/reports/
  notify_on: expired
```

```
数据存储:
  data/chekhov-guns/
    ├── active.yaml         # tracking + stale
    ├── archive.yaml        # resolved + expired
    └── reports/
```

**与 foreshadowing DAG 联动:** stale/expired 枪可一键导入 DAG；DAG 登记伏笔从枪追踪器移除（避免重复）

**与 author-notes 联动:** 过期枪处理记录写入 author-notes；作者确认忽略 → 加入 ignore.yaml

---

> *"每一个被遗忘的细节，都是读者对作者信任的一次裂缝。"*
