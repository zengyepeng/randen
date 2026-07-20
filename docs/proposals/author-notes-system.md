# 作者笔记系统 — 燃灯 P0 设计

> 设计日期: 2026-07-19 | 状态: 提案 | 优先级: P0
>
> 核心原则: **作者笔记不是一次性 prompt，而是贯穿整本书的"持续对话"。**

---

## 问题定义

### 当前短板

```
现有 author_intent.md + current_focus.md 机制:
  ✓ 能承载"长期不变的意图"和"当前阶段的创作罗盘"
  ✗ 但缺少一个关键环节：作者的即时反馈循环

作者的心路历程:
  - 写到第 50 章: "我想在这个部分多写一些日常"
  - 写到第 100 章: "不对，节奏太慢了，接下来全部加速"
  - 写到第 200 章: "主角的成长弧线偏了，需要拉回来"
  → 这些想法散落在聊天记录里，不构成结构化约束
  → AI 不知道作者"现在"在想什么
```

### 核心洞察

> **作者与 AI 的关系不是"下达任务→等待结果"的一次性交互，而是"持续调校→共同成长"的创作伙伴关系。作者笔记系统就是这个关系的载体。**

```
作者笔记系统 = 全局笔记 + 卷级笔记 + 章级笔记 + 主动询问机制 + 笔记演化
```

---

## 一、作者笔记的三层架构

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────┐
│  L1: 全局笔记 (author_intent.md)                         │
│  ├─ 已存在于 src/story/                                  │
│  ├─ 修改频率: 极低（每 50-100 章回顾一次）                │
│  ├─ 内容: 全书的核心追求、不变的主题、绝不妥协的红线       │
│  └─ 生效方式: 始终加载，作为所有章节的底层底色              │
├─────────────────────────────────────────────────────────┤
│  L2: 卷级笔记 (volume_note.md) ← 新增                    │
│  ├─ 存储于 src/chapter_notes/volume_N_note.md            │
│  ├─ 修改频率: 每卷开始时写一次，卷中微调 1-2 次            │
│  ├─ 内容: 这一卷我要达成什么                              │
│  └─ 生效方式: 卷内所有章节始终加载                         │
├─────────────────────────────────────────────────────────┤
│  L3: 章级笔记 (chapter_note.md) ← 新增                   │
│  ├─ 存储于 src/chapter_notes/ch_XXX_note.md              │
│  ├─ 修改频率: 每章可写                                 │
│  ├─ 内容: 本章想要的感觉 + 必须场景 + 绝不要的             │
│  └─ 生效方式: 仅当前章加载（详见《人类第一稿机制》）       │
└─────────────────────────────────────────────────────────┘
```

### 1.2 L1: 全局笔记 — author_intent.md

已有文件，补充使用方式。

```markdown
# 作者全局意图 (author_intent.md)

## 我要讲一个什么样的故事
一个关于「信任」的故事。在一个互相猜忌的修真世界里，
主角选择相信——不是天真，而是一种有代价的、深思熟虑的选择。

## 这本书不可动摇的核心
- 主角永远不会用卑劣手段取胜
- 每一个反派都有完整的动机——哪怕读者讨厌他，也必须理解他
- 力量体系是"减法"——越往上走，能用的力量越少，选择越受限

## 我要给读者什么
- 60% 燃 + 25% 痛 + 15% 治愈
- 每 3 章至少一个"让读者拍大腿"的瞬间
- 结尾不让读者觉得"烂尾"

## 我的红线
- 不写爽文的降智反派
- 不写无逻辑的"机缘巧合"
- 不让女性角色沦为工具人
```

**使用方式**：始终注入 canonical packet，作为所有其他约束的「底层默认值」。

```python
# context_builder.py 中现有逻辑，保持不变
author_intent = self._load_story_control("author_intent.md", max_chars=3000)
# → 注入到 packet.author_intent
```

### 1.3 L2: 卷级笔记 — volume_note.md

新增文件类型。每卷开始前由青灯引导作者创建。

#### 格式模板

```markdown
# 卷级笔记 — 第三卷「北境烽烟」

> 创建日期: 2026-07-19 | 覆盖章节: ch_101-ch_200

## 这一卷我要达成什么

### 情节目标
- 帝国与北境的全面战争爆发
- 主角从一个「被卷入的人」变成一个「主动选择参战的人」
- 揭示北境异动的真正原因（非军事威胁，而是上古封印松动）

### 人物弧线
- 主角: 从「保护身边的人」扩展到「保护身后的人」——责任感的扩大
- 顾恒: 揭露其北境将军的真实身份，从神秘角色转为有血有肉的战士
- 林月: 从被动等待到主动行动——她的成长弧线在本卷完成转折

### 节奏设计
- 前半卷 (ch_101-150): 战争前夕的紧绷感——大量文戏
- 后半卷 (ch_151-200): 战争爆发——动作密度显著提高
- 关键节点:
  - ch_120: 谷口初战（小规模遭遇）
  - ch_150: 帝都陷落（全书第一个大高潮）
  - ch_180: 主角第一次指挥千军万马（成长里程碑）

## 这一卷我不要什么
- 不要主角突然天下无敌——力量成长必须吃力
- 不要让战争变成背景板——每一场战斗都要写实的代价
- 不要把北境写成纯粹的"恶"——给他们合理的动机

## 这一卷的风格
- 前半卷: 冷静、克制、暗流涌动（类似《冰与火之歌》前几卷）
- 后半卷: 残酷、直接、不留余地（类似《水浒传》战斗段落）
```

#### YAML 配置映射

```yaml
# novel_config.yaml 新增
volume_notes:
  enabled: true
  path: "src/chapter_notes/"        # 存储在 chapter_notes 目录
  pattern: "volume_{N}_note.md"     # 命名格式
  auto_load: true                   # 卷内所有章节自动加载
  max_chars: 2000                   # 注入 packet 的最大字符数
  
  # 青灯交互配置
  qingdeng:
    prompt_before_volume: true      # 每卷开始前主动询问
    require_approval: true          # 需要作者确认后才生效
    review_at_volume_end: true      # 每卷结束后回顾
```

#### 注入方式

```python
# context_builder.py 新增
def _load_volume_note(self, chapter_id: str) -> str:
    """根据章节 ID 加载对应的卷级笔记"""
    volume_num = self._get_volume_number(chapter_id)
    if volume_num == 0:
        return ""
    
    note_path = self.src_root / "chapter_notes" / f"volume_{volume_num}_note.md"
    if note_path.exists():
        text = note_path.read_text(encoding="utf-8").strip()
        return text[:2000]  # 注入限制 2000 字符
    return ""

def _get_volume_number(self, chapter_id: str) -> int:
    """根据章节 ID 推算卷号
    
    需要查阅 hierarchy 或 outline 中的卷-章映射。
    """
    hierarchy = self._load_outline_hierarchy()
    arc = hierarchy.get_parent_arc(chapter_id)
    if arc:
        match = re.search(r'(\d+)', arc.node_id)
        return int(match.group(1)) if match else 0
    return 0
```

### 1.4 L3: 章级笔记 — chapter_note.md

详见《人类第一稿机制》（`human-first-draft.md`）。此处仅补充与卷级/全局笔记的关系。

```yaml
# 章级笔记配置
chapter_notes:
  enabled: true
  path: "src/chapter_notes/"
  pattern: "{chapter_id}_note.md"
  optional: true                    # 章级笔记不是必须的
  max_chars_per_note: 1000          # 单章笔记上限
  
  # 会话策略（与青灯联动）
  session_strategy:
    ask_every: null                  # 不用每章都问——太烦人
    ask_when:                        # 只在以下几种情况主动询问
      - "转折章节"                   # 大纲标记为 turning_point 的章节
      - "情绪高峰章节"               # 大纲标记为 climax 的章节
      - "作者主动触发"               # 作者在青灯中说"这章我要写笔记"
      - "连续 10 章无笔记后"          # 太久没写，提醒一下
```

---

## 二、笔记的生效方式：约束层叠加

### 2.1 约束层模型

作者笔记不是替换 AI 的判断，而是作为**约束层叠加**在 AI 的自由创作之上。

```
┌──────────────────────────────────────────────────────┐
│                    AI 自由创作空间                     │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │          风格合成 (composed style)            │    │
│  │  技法框架: 句长/对话率/节奏/描写密度           │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │         作者人设 (author persona)              │    │
│  │  长期底色: 语言指纹/人物观/情感调色盘           │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │        创作罗盘 (current_focus)                │    │
│  │  阶段方向: 当前 30 章的核心关注点              │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │     ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓          │    │
│  │     ┃  作者笔记系统 (三层)          ┃          │    │
│  │     ┃                            ┃          │    │
│  │     ┃  L1 全局 → 底层默认          ┃          │    │
│  │     ┃  L2 卷级 → 当前卷的方向约束  ┃          │    │
│  │     ┃  L3 章级 → 本章的最高优先级   ┃          │    │
│  │     ┃          (覆盖上述所有)      ┃          │    │
│  │     ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛          │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  AI 在约束层限定的范围内自由创作                       │
└──────────────────────────────────────────────────────┘
```

### 2.2 优先级与冲突消解

```python
class ConstraintLayer:
    """约束层管理器"""
    
    def resolve(self, layers: List[ConstraintLayer]) -> ResolvedConstraints:
        """多层约束的冲突消解
        
        规则:
        1. 章级 > 卷级 > 全局
        2. 作者笔记 > 作者人设 > 风格合成
        3. 「绝不要的」> 「必须出现的」> 「想要的」
        """
        resolved = ResolvedConstraints()
        
        # 从底向上叠加
        for layer in sorted(layers, key=lambda l: l.priority):
            resolved = resolved.merge(layer, conflict_policy='higher_wins')
        
        return resolved


# 具体的冲突消解示例
CONFLICT_RESOLUTION_EXAMPLES = {
    "章级「绝不要回忆杀」 vs 卷级「本卷需要 3 处关键回忆」": {
        "resolution": "章级胜出。该章不写回忆杀。回忆杀安排到卷内其他章节。",
        "rule": "章级硬约束 > 卷级建议",
    },
    "章级「想要压抑感」 vs 人设「语言明亮积极」": {
        "resolution": "章级胜出。本章情绪语调调整为压抑。",
        "rule": "章级情绪约束 > 长期人设",
    },
    "章级未指定禁用词 vs 人设 hard_no_phrases": {
        "resolution": "人设的禁用词继续生效。",
        "rule": "笔记不覆盖 = 下层继续生效",
    },
    "卷级「前半卷冷静克制」 vs 章级「本章要激烈战斗」": {
        "resolution": "章级胜出。但卷级提示在本章写完后仍有效——一个战斗章不会改变整卷基调。",
        "rule": "章级优先级更高，但不影响卷级对其他章的约束",
    },
}
```

### 2.3 生效范围

```
┌──────────┬────────┬────────┬──────────┬────────────┐
│ 约束层    │ 加载时机│ 生效范围 │ 可被覆盖 │ 覆盖来源    │
├──────────┼────────┼────────┼──────────┼────────────┤
│ 全局笔记  │ 始终   │ 所有章  │ ✓       │ 卷级/章级  │
│ 卷级笔记  │ 卷内   │ 该卷所有章│ ✓      │ 章级     │
│ 章级笔记  │ 单章   │ 仅该章  │ ✗       │ (无)     │
│ 作者人设  │ 始终   │ 所有章  │ ✓       │ 层笔记    │
│ 创作罗盘  │ 始终   │ 所有章  │ ✓       │ 卷级/章级  │
│ 风格合成  │ 始终   │ 所有章  │ ✓       │ 人设+笔记  │
└──────────┴────────┴────────┴──────────┴────────────┘
```

---

## 三、青灯的主动询问机制

### 3.1 设计理念

> **青灯不是一个被动的资料库，而是一个关心「作者在想什么」的编辑。**

### 3.2 三种触发场景

#### 场景 1: 里程碑检查（每 10 章）

```
触发: 当青灯检测到「已连续写了 10 章，作者未和青灯交互」
行为: 青灯主动发一条消息
```

```markdown
# 青灯: 里程碑检查 — ch_140

> 从 ch_131 到 ch_140，你已经连续写了 10 章。
> 在落笔开始下一章之前，想和你同步一下感觉：

- 这 10 章的节奏，你满意吗？
- 有什么你之前想写，但还没写到的东西吗？
- 有没有哪个角色你心里觉得「好像不太对」？

（如果一切都好，回复「继续」就行。不用勉强。）
```

**检查维度**：

```yaml
qingdeng_milestone_check:
  every_n_chapters: 10
  
  dimensions:
    - id: "pacing_satisfaction"
      question: "节奏快慢合适吗？"
      options: ["太慢了", "刚好", "太快了"]
      
    - id: "character_accuracy"
      question: "角色的行为和性格，目前符合你的预期吗？"
      options: ["完全符合", "个别有偏差", "很多都不对"]
      follow_up: "哪些角色需要调整？具体哪方面？"
      
    - id: "missing_elements"
      question: "有想写但还没写到的内容吗？"
      type: "open"  # 开放回答
      
    - id: "direction_check"
      question: "接下来的 10 章，方向需要调整吗？"
      type: "open"
      
    - id: "tone_check"
      question: "整体的情绪基调，还在你要的频道上吗？"
      options: ["完美", "略有偏差", "偏得有点远"]
```

#### 场景 2: 卷终回顾（每卷结束）

```
触发: 当青灯检测到当前卷的所有章节已完成
行为: 青灯生成一份回顾，提出下一卷的方向草案
```

```markdown
# 青灯: 卷终回顾 — 第三卷「北境烽烟」

## 📊 本卷数据
- 章节: ch_101 ~ ch_200 (100 章)
- 总字数: 约 35 万字
- 出场角色: 23 人（新增 8 人）
- 新开伏笔: 12 条 / 已闭合: 7 条 / 遗留: 5 条

## 📝 你的笔记回顾
- 卷级笔记: "前半卷冷静克制，后半卷残酷直接"
- 章级笔记: 写了 15 章（覆盖率 15%）
  - 高频关键词: 压抑、暗流、代价、脏
  - 高频「绝不要」: 主角开挂 (6 次)、回忆杀 (4 次)

## 🎯 目标达成率
- 情节目标: 3/3 完成 ✅
- 人物弧线: 2/3 完成 (顾恒角色深度 ⚠️ 待下一卷)
- 节奏设计: 基本符合预期

## ❓ 下一卷的方向
根据之前的规划，第四卷「天道重现」的核心是揭露上古秘密。
但你在 ch_180 的笔记中提到了「想多一些日常」。

我的草案:
1. 第四卷分两部分: 前半 (ch_201-250) 偏日常/铺垫，后半 (ch_251-300) 推进主线
2. 或者保持原计划，在卷中穿插 2-3 章日常作为喘息

你怎么想？
```

#### 场景 3: 重大转折确认

```
触发: 当下一章大纲标记为 turning_point、climax、character_death 等
行为: 青灯在章节开始前主动询问
```

```yaml
qingdeng_pivotal_check:
  triggers:
    - outline_node_type: "turning_point"
      message: "下一章是一个转折点。确认一下你的设计意图？"
    - outline_node_type: "climax"
      message: "高潮章来了。有什么特别的情绪/画面要求吗？"
    - character_death: true
      message: "下一章有角色退场。要不要先写一份章级笔记来定调？"
    - major_revelation: true
      message: "下章有重大揭示。这个揭示的感觉你希望是「震撼」还是「隐晦」？"
```

### 3.3 防骚扰机制

```python
class QingdengInteractionPolicy:
    """青灯交互策略——确保不变成骚扰"""
    
    # 主动询问的冷却期
    COOLDOWN_CHAPTERS = 5  # 两次主动询问之间至少间隔 5 章
    
    # 沉默窗口
    SILENT_WINDOW_START = 23  # 晚上 11 点到早上 7 点不主动
    SILENT_WINDOW_END = 7
    
    # 紧急例外（即使在冷却期也不跳过）
    EMERGENCY_TRIGGERS = [
        "连续 3 章审查报告出现同一警告",
        "伏笔超 3 卷未闭合且即将进入新卷",
        "风格漂移超 2σ",
    ]
    
    def should_ask(self, chapter_id: str, last_ask_chapter: int) -> bool:
        """判断是否应该主动询问"""
        current = int(re.search(r'(\d+)', chapter_id).group(1))
        
        # 冷却期检查
        if current - last_ask_chapter < self.COOLDOWN_CHAPTERS:
            return False
        
        # 时间检查
        now = datetime.now()
        if self.SILENT_WINDOW_START <= now.hour or now.hour < self.SILENT_WINDOW_END:
            return False
        
        return True
```

---

## 四、笔记的演化

### 4.1 设计原则

> **作者的想法会变——这是正常的。笔记系统应忠实记录这个变化，而不是试图抹掉它。**

```
处理变更的三个原则:
  1. 不覆盖旧笔记 — 旧笔记是创作的「化石层」，保留作为上下文
  2. 添加变更记录 — 每次修改生成一条变更记录，带有时间戳和原因
  3. 最新笔记优先 — 写作时取最新版本，但允许参考历史版本
```

### 4.2 变更记录格式与历史管理

```yaml
# src/chapter_notes/ch_120_changelog.yaml
- timestamp: "2026-07-15 14:30"
  modified_section: "想要的感觉"
  old_value: "紧张、一触即发的气氛"
  new_value: "表面松弛、暗中紧绷"
  reason: "作者觉得'紧张'太直白，想要更微妙的感觉"
```

```python
class NoteHistory:
    """笔记历史版本管理器"""
    
    def get_evolution(self, note_path: Path) -> List[NoteVersion]:
        """获取笔记的完整演化历史"""
        changelog = self._load_changelog(note_path)
        return [NoteVersion(timestamp=e.timestamp, reason=e.reason) for e in changelog]
    
    def get_version(self, note_path: Path, timestamp: str) -> str:
        """通过反向应用 changelog 重建指定时间点的版本"""
        current = note_path.read_text(encoding="utf-8")
        for entry in reversed(self._load_changelog(note_path)):
            if entry.timestamp > timestamp:
                current = self._undo_change(current, entry)
        return current
```

### 4.3 笔记演化示例

```
ch_001: 「神秘、引人入胜」
  ↓
ch_051: 「第一次真正的「痛」，不煽情但要让人记住」(作者回顾后调整)
  ↓
ch_201: 「回到日常。憋了一百章的轻松感」(卷终回顾后调整)
  ↓
ch_500: 「终局。笔要稳，不能慌。读者跟了这么久，要对得起他们。」

→ 这些不是风格"漂移"，而是有意图的"演化"
→ 笔记系统忠实地记录了这条演化路径
```

---

## 五、与作者人设的关系

### 5.1 分工定义

```
作者人设 (author persona):  长期不变的创作身份
                             → "我是一个什么样的人，在讲一个什么样的故事"

作者笔记 (author notes):    当前阶段的具体指引
                             → "我现在想让这个故事往哪个方向走"
```

| 维度 | 作者人设 | 作者笔记 |
|------|---------|---------|
| 性质 | 底色 | 颜料 |
| 稳定度 | 极高（50 章才回顾） | 可逐卷/逐章变化 |
| 粒度 | "我是一个什么样的人" | "现在我想怎么做" |
| 优先级 | 低（可被笔记覆盖） | 高（章级笔记最高） |
| 变更频率 | 极低 | 自由 |
| 生效方式 | 作为默认值 | 作为覆盖层 |

### 5.2 具体关系

```
关系 1: 笔记是人设的「当前实现」

人设说: "我喜欢描写动作多过心理活动"
卷级笔记说: "这一卷心理活动比例提高到 30%——因为主角在经历身份危机"
→ 笔记不矛盾于人设——它是在人设框架内的「阶段性侧重调整」

关系 2: 笔记可以临时「借用」不属于人设的风格

人设说: "我的语言干净克制，不堆砌形容词"
章级笔记说: "这一章大量写道具/服装细节——因为主角第一次参加正式宴会，
          这种场合的细节本身就是一种叙事"
→ 笔记在这一章"借用"了一种不属于人设的写法——这是有意识的技巧，不是漂移

关系 3: 笔记的演化轨迹反映人设的成熟过程

前 100 章: 笔记高频出现"不要太慢""加速" 
→ AI 自动分析 → 建议: "你的 natural pacing 可能是偏慢的，要不要更新人设中的节奏偏好？"

后 300 章: 笔记高频出现"留白""不说破"
→ AI 自动分析 → 建议: "你越来越倾向含蓄表达，人设中的'语言风格'可能已经过时了"
```

### 5.3 人设回顾触发

```python
class PersonaEvolutionDetector:
    """检测笔记变化是否意味着人设需要更新"""
    
    THRESHOLD = 10  # 连续 N 章笔记趋势与当前人设不一致时提醒
    
    def analyze(self, notes: List[ChapterNote], persona: AuthorPersona) -> PersonaUpdateSuggestion:
        """分析最近笔记趋势 vs 人设设定"""
        # 检查: 最近笔记「绝不要」高频约束某个方向，而人设尚不支持该方向
        narrative_constraints = [
            n for n in notes[-50:]
            if any(kw in n.never_do for kw in ['心理描写', '煽情', '形容词'])
        ]
        if len(narrative_constraints) > self.THRESHOLD:
            return PersonaUpdateSuggestion(
                trigger="笔记趋势与人设出现持续偏差",
                suggestion="你的人设 narrative_attitude 还是「悲悯」，但近期笔记持续约束情感表达——要更新人设吗？",
            )
        return PersonaUpdateSuggestion(trigger=None, suggestion="人设与笔记一致")

---

## 六、实施文件与集成

### 6.1 新增文件

```
src/
├── chapter_notes/
│   ├── volume_1_note.md           # 第一卷笔记
│   ├── volume_2_note.md           # 第二卷笔记
│   ├── ch_001_note.md             # 章节笔记（可选）
│   ├── ch_002_note.md
│   └── ...
│
data/ (运行态)
└── chapter_notes/
    └── changelogs/
        ├── ch_001_changelog.yaml   # 变更记录
        └── ...
```

### 6.2 需要修改的文件

| 文件 | 改动 | 优先级 |
|------|------|--------|
| `models/context_package.py` | GenerationContext 新增 `volume_note` 字段 | P0 |
| `tools/context_builder.py` | 新增 `_load_volume_note()`，注入三层笔记到 context | P0 |
| `tools/chapter_assembler.py` | 新增 volume_note 加载和注入逻辑 | P0 |
| `tools/agent/writer.py` | creative_write prompt 中纳入三层笔记约束 | P0 |
| `skills/qingdeng-agent/SKILL.md` | 新增里程碑检查、卷终回顾、转折确认流程 | P0 |
| `novel_config.yaml` | 新增 `author_notes` 配置段 | P1 |
| `tools/post_validator.py` | 新增「笔记合规」维度——检查 AI 输出是否遵守笔记约束 | P1 |
| `tools/state_validator.py` | 新增笔记变更记录自动写入逻辑 | P2 |

### 6.3 完整配置示例

```yaml
# novel_config.yaml — author_notes 完整配置段

author_notes:
  enabled: true
  
  global:
    path: "src/story/author_intent.md"
    max_chars_in_context: 3000
  
  volume:
    path: "src/chapter_notes/"
    pattern: "volume_{n}_note.md"
    max_chars_in_context: 2000
  
  chapter:
    path: "src/chapter_notes/"
    pattern: "{chapter_id}_note.md"
    max_chars_per_note: 1000
    expansion_ratio: 10
  
  # 约束层优先级 (数值越大越高)
  priority:
    hard_negatives: 100
    must_include: 90
    desired_feeling: 80
    volume_direction: 60
    creative_focus: 50
    persona: 40
    composed_style: 30
    global_intent: 20
    experimental: 10
  
  # 青灯交互
  qingdeng:
    milestone_check:
      every_n_chapters: 10
      cooldown_chapters: 5
    volume_review:
      auto_generate: true
    pivotal_moment:
      triggers: [turning_point, climax, character_death, major_revelation]
    quiet_hours: { start: 23, end: 7 }
  
  # 笔记演化
  evolution:
    changelog_enabled: true
    changelog_path: "data/chapter_notes/changelogs/"
    auto_detect_persona_drift: true
    persona_drift_threshold: 10
  
  # 审查
  review:
    note_compliance_check: true
    check_dimensions: [hard_negatives_obeyed, must_include_present, feeling_alignment]
```

---

## 七、端到端流程示例

### 场景：第一卷写完，进入第二卷

```
Step 1: 青灯检测到卷结束
  → 生成卷终回顾报告
  → 发送给作者

Step 2: 作者看回顾
  → 确认哪些达成了、哪些没达成
  → 回答青灯提出的「下一卷方向」问题
  → 青灯生成 volume_2_note.md 草案

Step 3: 作者看草案，修改确认
  → 青灯保存 volume_2_note.md

Step 4: ch_051-ch_060 (第二卷开头)
  → 每一章的 canonical packet 自动加载:
    - L1: author_intent.md (全书底色)
    - L2: volume_2_note.md (第二卷方向)
    - L3: ch_XXX_note.md (如果作者写了章级笔记)
  → 冲突消解: 章级 > 卷级 > 全局

Step 5: ch_060 — 里程碑检查
  → 青灯: "从 ch_051 到 ch_060 写了 10 章，你感觉怎么样？"
  → 作者: "第二卷的方向对了，继续保持"
  → 青灯: "收到。"
  → 青灯更新 milestone log: ch060_author_satisfaction = "positive"

Step 6: ch_100 — 第二卷结束
  → 青灯生成卷终回顾
  → 对比 volume_2_note.md 的目标 vs 实际
  → 分析笔记演化趋势
  → 提出第三卷方向草案
  → 循环...
```

---

> *"好的创作工具不替你决定，而是帮你记录「我是怎么走过来的」。"*
> *—— 作者笔记系统设计原则*
