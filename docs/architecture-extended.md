# 燃灯 — 几千万字级长篇小说扩展架构设计

> 设计日期: 2026-07-19 | 目标规模: 1000万-5000万字 (2000-10000章)

---

## 问题定义

当前燃灯 v1.0 的 canonical packet 设计在 100 章以内表现优秀，但在 2000+ 章量级下会面临：

| 瓶颈 | 100 章 | 2000 章 | 恶化倍数 |
|------|--------|---------|----------|
| 章节记忆总量 | 100 × 500 token = 5万 | 2000 × 500 = 100万 | 20x |
| 伏笔 DAG 节点 | 20-50 | 200-500 | 10x |
| 真相文件大小 | ~5KB | ~100KB+ | 20x |
| 角色演变轨迹 | 5-10 条 | 50-100+ 条 | 10x |
| 上下文窗口占用 | 30% | 750% (爆) | — |

**核心矛盾：模型上下文窗口线性增长的速度远低于小说文本的线性增长。**

---

## 一、金字塔记忆系统

### 1.1 架构

```
┌─────────────────────────────────────────────────────────┐
│  L3: 全局索引 (Global Index) — 永远加载，~2,000 tokens   │
│  ├─ 核心角色列表 (≤15人) + 一句话定位 + 状态标记          │
│  ├─ 世界规则摘要 (≤500 字)                                │
│  ├─ 各卷一句话总结 (每卷1行)                              │
│  ├─ 未闭合跨卷伏笔列表 (≤20条)                            │
│  └─ 风格基线快照 (句式分布/对话率/情绪密度的数值摘要)      │
├─────────────────────────────────────────────────────────┤
│  L2: 卷级记忆 (Volume Memory) — 按需加载，~3,000 tokens   │
│  ├─ 当前卷情节脉络 (50-100章压缩为2-3页叙事摘要)          │
│  ├─ 人物弧线状态 (每个核心角色在当前卷的起点→终点)         │
│  ├─ 卷内闭合/新开伏笔 (标记 resolved/pending/orphan)       │
│  ├─ 关键对话/场景锚点 (每章1-2个关键词，供语义检索)        │
│  └─ 卷级风格快照 (与全局基线的差异)                       │
├─────────────────────────────────────────────────────────┤
│  L1: 章级记忆 (Chapter Memory) — 动态加载                  │
│  ├─ 近3章完整摘要 (始终加载，~1,500 tokens)                │
│  ├─ 语义检索命中章 (向量搜索 → 只加载相关的，按需)          │
│  └─ 每章摘要格式:                                         │
│      { 情节: 2-3句, 人物状态变更: 列表,                   │
│        新伏笔: [f_id], 闭合伏笔: [f_id],                  │
│        情感基调: 词, 关键对话片段: 2-3句,                  │
│        token用量: {写作/观察/结算} }                       │
└─────────────────────────────────────────────────────────┘
```

### 1.2 语义检索机制

```
第 1500 章需要引用"玉佩"的伏笔：

旧方案: 遍历 1499 章记忆 → 300K+ token → 炸裂
新方案:
  1. 向量检索 "玉佩" → 命中 8 章 (分布在卷3/卷7/卷12)
  2. 只加载这 8 章的 L1 记忆 → ~4,000 tokens
  3. 优先加载最近的命中 + 首次出现的命中

语义检索索引:
  data/memory/index/embedding_index.pkl   # Faiss/Chroma 向量索引
  每章存储: embedding(章节摘要) + 关键词列表 + 出场人物

检索策略（四优先级）:
  Priority 1: 当前卷内的相关章节 (权重 1.0)
  Priority 2: 最近2卷内的相关章节 (权重 0.7)
  Priority 3: 关键转折点的相关章节 (权重 0.5)
  Priority 4: 更早卷的相关章节 (权重 0.3, 最多取3个)
```

### 1.3 记忆压缩管道

```
每写完一章:
  生成 L1 章级记忆 (500 token) → 写入 data/memory/chapters/
  更新向量索引 → 计算章节摘要 embedding

每写完一卷 (50-100章):
  汇总本卷所有 L1 记忆 → LLM 压缩为 L2 卷级记忆 (3,000 token)
  仅保留前3卷的 L1 记忆可检索，更早的标记为归档
  更新 L3 全局索引中的本卷一句话总结

每写完 5 卷:
  汇总最近 5 卷的 L2 记忆 → 检查 L3 是否需要更新
  归档陈旧 L1 记忆 (>500章前的) → data/archive/
```

---

## 二、真相文件分层与增量更新

### 2.1 分层设计

```
data/truth/
├── global/                      # 全局常量 — 写好后基本不变
│   ├── world_rules.md           # 世界规则（力量体系、社会制度）
│   ├── character_archetypes.md  # 角色原型（核心设定的不可变部分）
│   └── timeline_epochs.md       # 纪元/大事件时间线
│
├── active/                      # 当前卷活跃状态 — 每章更新
│   ├── current_state.yaml       # 当前状态（增量式，不重建全量）
│   │   格式: { entity_id: { location, status, last_seen_chapter } }
│   ├── relationships.yaml       # 人物关系（带章节来源标注）
│   │   格式: { pair: { relation, intensity, last_updated_chapter } }
│   └── ledger.yaml              # 资源账本（财富/道具/技能等级）
│      格式: { character_id: { resource: { amount, last_change_chapter } } }
│
└── archive/                     # 历史卷封存 — 永不修改
    ├── vol_001_state.yaml       # 第一卷结束时的完整快照
    ├── vol_002_state.yaml
    └── ...
```

### 2.2 增量更新协议

```
旧方案（重建全量）:
  读取旧 state → 修改 → 写回完整 state
  问题: state 文件随章节数线性增长，读/写开销越来越大

新方案（增量更新）:
  每章写入一个 delta 文件:
    data/truth/active/deltas/ch_0150_delta.yaml
    格式: { add: [...], modify: [...], remove: [...] }

  当前状态 = 最近一次全量快照 + 之后所有 delta 的合并结果

  每卷结束时:
    应用所有 delta → 生成全量快照 → 清理 delta
    封存旧快照到 archive/

  日常读取:
    加载最近全量快照 + 最新 delta 链 → 内存合并 → 极快
    写入: 追加一个 delta 文件 → 毫秒级
```

---

## 三、伏笔生命周期管理

### 3.1 三级伏笔体系

```yaml
# data/foreshadowing/active.yaml  (当前卷未闭合，始终加载)
f001:
  title: "玉佩的真实来历"
  raised_in: ch_0123        # 提出章节
  last_touched: ch_0456     # 最后一次提及
  status: developing         # developing | climax | resolving
  priority: high             # high | medium | low
  estimated_resolve: ch_0600 # 预计闭合章节
  related_characters: [林月, 顾恒]
  summary: "玉佩在青河镇古墓中被发现，表面刻有上古符文..."
  cross_volume: false

# data/foreshadowing/pending.yaml  (跨卷未闭合)
f042:
  title: "帝国十二域的真正统治者"
  raised_in_chapter: ch_0120
  raised_in_volume: 1
  current_volume: 5
  status: developing
  cross_volume: true
  touched_in_volumes: [1, 3, 5]
  priority: high

# data/foreshadowing/resolved.yaml  (已闭合，存档)
f005:
  title: "白旭的身份之谜"
  resolved_in: ch_0089
  resolution_summary: "揭示白旭是前任帝国剑侍..."
```

### 3.2 自动生命周期

```
提出 (raised) → 发展中 (developing) → [卷内闭合 → resolved]
                                     → [未闭合 → 升级 pending]
                                     → [3卷未提及 → 标记 orphan → 提醒作者]

每章写完后自动扫描:
  1. 检查本章是否提及了 active 中的伏笔 → 更新 last_touched
  2. 检查本章是否闭合了某条伏笔 → 标记 resolved + 写入 resolution_summary
  3. 检查 active 中是否有超过 2 卷未提及的 → 标记 orphan → 在审查报告中提醒
```

---

## 四、上下文预算分配系统

### 4.1 预算模型

```
假设模型上下文窗口 = 128K tokens (约 6-8万汉字)

每章写作预算分配:
┌─────────────────────────┬──────────┬─────────────┐
│ 模块                    │ 占比     │ Token 数    │
├─────────────────────────┼──────────┼─────────────┤
│ 大纲窗口 (±3章)         │ 15%      │ ~19,000     │
│ 角色状态 (出场+核心)     │ 20%      │ ~25,000     │
│ 世界规则 (语义检索片段)  │ 8%       │ ~10,000     │
│ 风格约束 (合成+craft)   │ 10%      │ ~13,000     │
│ 历史记忆 (L3+L2+L1)     │ 25%      │ ~32,000     │
│ 伏笔 (active+相关pending)│ 7%       │ ~9,000      │
│ 上一章正文 (raw text)    │ 10%      │ ~13,000     │
│ 弹性缓冲                 │ 5%       │ ~7,000      │
├─────────────────────────┼──────────┼─────────────┤
│ 合计                    │ 100%     │ ~128,000    │
└─────────────────────────┴──────────┴─────────────┘
```

### 4.2 预算执行

```python
class ContextBudgetManager:
    """上下文预算管理器"""
    
    def allocate(self, packet: CanonicalPacket, budget: int = 128000):
        """按预算分配上下文，超出预算的模块自动降级压缩"""
        
        allocations = {
            'outline': budget * 0.15,
            'characters': budget * 0.20,
            'world_rules': budget * 0.08,
            'style': budget * 0.10,
            'memory': budget * 0.25,
            'foreshadowing': budget * 0.07,
            'previous_chapter': budget * 0.10,
            'buffer': budget * 0.05,
        }
        
        # 如果某个模块超预算 → 触发压缩
        for module, limit in allocations.items():
            if packet.size(module) > limit:
                packet.compress(module, target_size=limit)
        
        return packet
```

---

## 五、风格漂移监控

### 5.1 基线快照

```python
# 每 50 章自动取样
@dataclass
class StyleBaseline:
    chapter_range: tuple   # (50, 100)
    avg_sentence_length: float
    dialogue_ratio: float   # 对话占比
    paragraph_density: float # 每段字数
    emotion_distribution: dict  # 情绪标签分布
    top_words: list        # 高频词 Top 50
    pacing_score: float    # 节奏紧密度
    
    def compare(self, current: 'StyleBaseline') -> dict:
        """对比当前章节 vs 基线，返回漂移告警"""
        warnings = []
        if abs(self.dialogue_ratio - current.dialogue_ratio) > 0.15:
            warnings.append(f"对话占比漂移: {self.dialogue_ratio:.2f} → {current.dialogue_ratio:.2f}")
        if abs(self.avg_sentence_length - current.avg_sentence_length) > 10:
            warnings.append(f"平均句长漂移: {self.avg_sentence_length:.0f} → {current.avg_sentence_length:.0f}字")
        return warnings
```

### 5.2 漂移响应

```
轻微漂移 (<1σ):
  → 在审查报告中标注，不阻断
  → 写入 author_notes: "近50章对话比例下降，是否刻意？"

中度漂移 (1-2σ):
  → 审查报告中高亮 + 建议
  → 自动在 style composed 中加强偏离方向的约束

严重漂移 (>2σ):
  → 暂停写章
  → 生成完整的"风格回归分析"
  → 要求作者确认后再继续
```

---

## 六、卷级一致性守护进程

### 6.1 触发时机

```
每写完一卷 (50-100章) → 自动触发一致性审计
```

### 6.2 审计维度

```yaml
audit_dimensions:
  
  character_consistency:
    - 每个核心角色的出场密度是否合理 (不应连续30章缺席)
    - 角色性格是否有前后矛盾 (基于性格描述词的语义对比)
    - 关系演变是否连贯 (关系图谱的变化轨迹)
    - 角色是否有未被回收的独立剧情线
    
  world_consistency:
    - 力量体系/世界观规则是否被意外打破
    - 时间线是否有漏洞 (日期跳跃、事件顺序)
    - 地理空间是否矛盾 (人物同时出现在两地)
    - 社会制度/经济体系的逻辑一致性
    
  plot_consistency:
    - 本卷所有伏笔是否都有回收计划
    - 因果链是否完整 (重大事件→影响→结果)
    - 情节节奏是否符合卷级弧线设计
    - 是否有闲置超过2卷的"僵尸谜团"
    
  style_consistency:
    - 风格基线漂移检测
    - AI 痕迹浓度趋势 (是否随章节数增加而上升)
    - 对话质量退化检测
    
  continuity:
    - 卷-卷之间的衔接是否平滑 (前卷结尾 → 本卷开头)
    - 人物状态是否在卷间正确传递
    - 未闭合伏笔是否正确从上一卷继承
```

### 6.3 输出

```
输出: data/reviews/vol_005_audit.md

├─ 总分: 87/100
├─ 人物一致性: 92/100 ✅
├─ 世界一致性: 89/100 ✅
├─ 情节一致性: 82/100 ⚠️
│   └─ 警告: 伏笔 f042 "帝国真实统治者" 已3卷未提及
├─ 风格一致性: 84/100 ⚠️
│   └─ 建议: 对话比例从卷1的42%下降到32%，人物对话密度降低
└─ 连续性: 88/100 ✅
```

---

## 七、多卷分册机制

### 7.1 卷的定义

```
每卷: 50-100 章 (约 15-50 万字)
每卷独立拥有:
  ├─ 自己的 truth/active/ (当前卷状态)
  ├─ 自己的 foreshadowing/active.yaml (卷内伏笔)
  ├─ 自己的 memory/ (卷内章节记忆)
  └─ 继承的 global/truth + pending foreshadowing (跨卷共享)
```

### 7.2 跨卷状态传递

```yaml
# 卷结束时的 handoff 协议
volume_handoff:
  from_volume: 3
  to_volume: 4
  passing:
    global_truth: "继承（不变）"
    pending_foreshadowing:
      - f042 (帝国统治者, 3卷未闭合)
      - f088 (北境异动, 2卷未闭合)
    character_state_snapshot:
      林月: { location: 青云宗, power_level: 元婴初期, relationships: intact }
      顾恒: { location: 北境, power_level: 化神中期, relationships: intact }
    unresolved_conflicts:
      - "帝国与北境的战争一触即发"
      - "青云宗内部权力斗争尚未揭晓"
  archived:
    volume_3_memories: "压缩为 L2 卷级记忆，封存到 archive/"
    volume_3_truth: "全量快照封存到 archive/"
```

---

## 八、实施路线图

### Phase 1: 基础扩展 (v1.1)
- [ ] L1-L2-L3 金字塔记忆系统
- [ ] 上下文预算管理器
- [ ] 章节摘要 embedding 向量索引

### Phase 2: 智能检索 (v1.2)
- [ ] 语义检索集成 (Faiss/Chroma)
- [ ] 伏笔生命周期自动管理
- [ ] 风格基线快照 + 漂移检测

### Phase 3: 守护进程 (v1.3)
- [ ] 卷级一致性审计
- [ ] 增量真相文件更新
- [ ] 多卷分册机制

### Phase 4: 极限优化 (v2.0)
- [ ] 5000+ 章级别压力测试
- [ ] 自适应上下文预算 (根据章节类型动态调整)
- [ ] 分布式记忆存储 (支持跨设备写作)

---

> *"真正的好故事，不是一次性写完的。它是在不断回望、修正、深化的过程中，慢慢长出来的。"*
> *—— 燃灯架构设计原则*
