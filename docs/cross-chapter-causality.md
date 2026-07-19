# 燃灯 — 跨章节因果图

> 设计日期: 2026-07-19 | 目标: 标记章节间因果依赖，改一章即知影响范围 | 优先级: P2

---

## 问题定义

两千章小说中修改某一章，就像在雷区拔引信。

作者想改第 50 章"顾恒断的是左臂还是右臂？"→ 系统回答：

```
确认。以下 18 章需要重审:
  - 第 87 章: 左臂挡招动作 → 需调换
  - 第 142 章: "右臂的伤疤" → 位置不变
  - 第 211 章: 白旭包扎右臂 → 需改
  - 第 305 章: 林月触碰空空的右袖 → 需改
  - ...共 18 章
```

---

## 一、因果 DAG 构建

### 1.1 事件类型与 DAG

```python
# causality_dag.py
from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum

class EventType(Enum):
    PLOT_TURN = "plot_turn"           # 情节转折
    REVELATION = "revelation"         # 真相揭示
    CHARACTER_CHANGE = "char_change"  # 人物状态变更
    WORLD_CHANGE = "world_change"     # 世界规则变化
    RELATIONSHIP = "relationship"     # 关系变化
    ITEM_ACQUIRE = "item_acquire"     # 获得物品
    LORE_DROP = "lore_drop"           # 设定补充

@dataclass
class StoryEvent:
    id: str
    chapter: int
    event_type: EventType
    subject: str
    action: str
    detail: str
    affected_entities: List[str]
    preconditions: List[str] = field(default_factory=list)
    consequences: List[str] = field(default_factory=list)

@dataclass
class CausalityEdge:
    from_event: str
    to_event: str
    relation: str      # causes | enables | contradicts | resolves
    confidence: float  # 0-1
    impact: str        # critical | important | minor

class CausalityDAG:
    def __init__(self):
        self.events: Dict[str, StoryEvent] = {}
        self.edges: List[CausalityEdge] = []
    
    def add_event(self, ch, etype, subject, action, affected=None):
        eid = f"e{len(self.events):05d}"
        self.events[eid] = StoryEvent(id=eid, chapter=ch, event_type=etype,
            subject=subject, action=action, detail=action,
            affected_entities=affected or [])
        return eid
    
    def add_edge(self, fid, tid, relation="causes", confidence=1.0, impact="important"):
        self.edges.append(CausalityEdge(fid, tid, relation, confidence, impact))
        self.events[fid].consequences.append(tid)
        self.events[tid].preconditions.append(fid)
```

### 1.2 事件自动提取

```python
class AutoExtractor:
    def __init__(self, dag: CausalityDAG):
        self.dag = dag
    
    def scan_chapter(self, text: str, ch: int):
        ids = []
        # 提取转折事件
        for m in re.finditer(r'(?:就在这时|突然|意外|转折|变数|异变)(?:，.{5,50}?)', text):
            ids.append(self.dag.add_event(ch, EventType.PLOT_TURN, "转折", m.group(0)[:30]))
        # 提取人物状态变更
        for m in re.finditer(r'(?:突破|晋级|领悟|断[了]?[左右]?[手臂腿脚]|功力(?:大进|倒退|全失))', text):
            ids.append(self.dag.add_event(ch, EventType.CHARACTER_CHANGE, "状态", m.group(0)))
        # 自动链接因果
        self._auto_link(ch, ids)
    
    def _auto_link(self, ch, new_ids):
        for nid in new_ids:
            for oid, oe in list(self.dag.events.items())[-200:]:
                if oe.chapter >= ch: continue
                shared = set(oe.affected_entities) & set(self.dag.events[nid].affected_entities)
                if shared and self._gap_ok(oe.chapter, ch):
                    self.dag.add_edge(oid, nid, "causes", 0.7, "important")
    
    def _gap_ok(self, old_ch, new_ch):
        return abs(new_ch - old_ch) < 300
```

### 1.3 手动标注接口（补充 AI 检测）

```yaml
# data/causality/manual_links.yaml
manual_links:
  - from: e00123    # 第50章 顾恒断臂
    to: e00456      # 第203章 左手剑术
    relation: causes
    note: "断臂直接导致他开发左手剑术"
  - from: e00345    # 第300章 灵气来自天地
    to: e01012      # 第800章 灵气来自人心
    relation: contradicts
    note: "??? 前文说天地，后文说人心——矛盾"
```

---

## 二、改动影响分析

```python
class ImpactAnalyzer:
    def __init__(self, dag: CausalityDAG):
        self.dag = dag
    
    def analyze(self, ch: int, desc: str) -> dict:
        events = [e for e in self.dag.events.values() if e.chapter == ch]
        if not events:
            return {"affected": [], "note": f"第{ch}章未登记，无追溯数据"}
        affected = set()
        for se in events:
            q, seen = [(se, [se.id])], set()
            while q:
                cur, path = q.pop(0)
                for edge in self.dag.edges:
                    if edge.from_event == cur.id:
                        ne = self.dag.events[edge.to_event]
                        affected.add(ne.chapter)
                        if ne.id not in seen:
                            seen.add(ne.id)
                            q.append((ne, path + [ne.id]))
        return {
            "change": desc,
            "total": len(affected),
            "chapters": sorted(affected),
            "recommendation": f"确认。以下 {len(affected)} 章需要重审。"
        }
```

### 输出示例

```markdown
# ⚠️ 跨章节影响分析报告
变动: 第50章「顾恒断左臂」→ 改为右臂

## 影响概览
直接事件: 3个 | 级联影响: 18章（第87-920章）| 关键: 5条 | 重要: 12条

## 关键影响链
⚠️ 断臂→挡招冲突: 第87章左臂挡招→第211章包扎→第305章触碰空袖
   → 需修改: 挡招、包扎、空袖（3处）
⚠️ 断臂→剑术链: 第203章左手剑→第310章比武→第450章剑术大成
   → 无需修改（断右臂则左手剑逻辑不变）
📌 情感线索: 第305章林月触碰空袖 → "右袖"→"左袖"（1处）

## 因果矛盾检测
❌ 第300章「灵气来自天地」vs 第800章「灵气来自人心」
   → 设定前后矛盾（不在本改动范围，但建议关注）
```

---

## 三、冲突检测

```yaml
# config/cross-chapter-causality.yaml
conflict_detection:
  direct_contradiction:
    description: "同一事实前后矛盾"
    method: "subjects match + action=contradictory"
  timeline_anomaly:
    description: "时间线逻辑错误（A前提是B，但A在B之前）"
    method: "temporal_order_check"
  causality_loop:
    description: "3+ 节点因果循环"
    method: "cycle_detection"
```

---

## 四、集成方案

```yaml
# config/cross-chapter-causality.yaml
enabled: true
run_on: post_chapter
extraction:
  event_types:
    - plot_turn / revelation / character_change / world_change
    - relationship / lore_drop / item_acquire
  auto_link:
    enabled: true
    min_confidence: 0.5
    max_lookback: 200
impact_analysis:
  max_chains: 15
  require_confirmation: true
conflict_detection:
  direct_contradiction: true
  timeline_anomaly: true
  causality_loop: true
output:
  report_dir: data/causality/reports/
  format: markdown
```

```
数据存储:
  data/causality/
    ├── dag.yaml                # 全量 DAG
    ├── events/vol_*_events.yaml
    ├── manual_links.yaml
    └── conflicts.yaml
```

---

> *"改一句台词，牵一发动全身。因果图不是枷锁——是告诉你哪些锁链牵不得。"*
