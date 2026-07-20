# 人类第一稿机制 — 燃灯 P0 设计

> 设计日期: 2026-07-19 | 状态: 提案 | 优先级: P0
>
> 核心原则: **不应该是"AI 写 3000 字→人类改"，而应该是"人类写 300-500 字灵感草稿→AI 扩展为 3000 字→保持人类的灵魂"**

---

## 问题定义

### 当前流程的痛点

```
传统 AI 辅助写作流程:
  1. 人类: "帮我写一场雨中的离别"
  2. AI: 输出 3000 字 → 人类读 → 发现:
     a. 感觉不对（太煽情/太冷淡）
     b. 漏掉了人类心中最重要的细节
     c. 加入了人类不想要的元素
  3. 人类: 标注要改的地方 → AI: 重写 → 循环...
```

**核心问题**：

| 问题 | 根源 | 后果 |
|------|------|------|
| AI 代写了人类的构思过程 | 人类只给了模糊指令 | 输出是 AI 的审美，不是人类的 |
| 修改成本极高 | 3000 字中改一处可能影响全局连贯性 | 越改越不像"自己的作品" |
| 人类在流程中处于被动位置 | 评估者而非创作者 | 创作满足感丧失，长期写作动力下降 |
| AI 的"作者声音"侵蚀 | 连续多章后风格趋同 | 读者感觉"像 ChatGPT 写的" |

### 人类第一稿的核心洞察

> **人类的长处是"知道想要什么"，AI 的长处是"把东西写出来"。流程应该放大各自的长处。**

```
人类第一稿流程:
  1. 人类: 写下 300-500 字的「作者笔记」—— 本章想要的感觉 + 必须出现的场景 + 绝对不要的
  2. AI: 严格遵循笔记，将 500 字扩展为 3000 字正文
  3. 人类: 读 3000 字 → 确认"这是我想要的" 或 调整笔记后重试

对比传统流程:
  - 人类投入降低: 从"读 3000 字→详细标注→等重写→再读" 降为 "读 3000 字→确认/微调笔记"
  - 创作控制力提升: 人类不是在改 AI 的作文，而是在设计蓝图
  - 满足感: 300 字中的每一句话都是自己要的 → 3000 字虽然大部分是 AI 写的，但灵魂是人类的
```

---

## 一、工作流设计

### 1.1 青灯规划阶段 — 创建作者笔记

在青灯（Qingdeng）规划会话中，每章大纲确定后，作者可以选择为本章写一份作者笔记。

```
用户 → 青灯
    │
    ├─ 1. 确定本章大纲 (outline.md 中已有)
    │
    ├─ 2. 青灯: "要为本章写一份作者笔记吗？"
    │       └─ 作者: 写 300-500 字笔记
    │
    ├─ 3. 青灯检查笔记质量:
    │     ├─ 是否包含了"想要的感觉"？
    │     ├─ 是否包含了至少一个"必须出现的场景"？
    │     └─ 如果笔记太短/太模糊 → 追问补充
    │
    ├─ 4. 笔记保存到 src/chapter_notes/ch_XXX_note.md
    │
    └─ 5. Handoff → 落笔写作阶段
```

### 1.2 落笔写作阶段 — 自动注入笔记

落笔（Luobi）在组装 canonical packet 时，自动检测是否存在当前章节的作者笔记：

```python
# 伪代码: chapter_assembler.py / context_builder.py
def assemble(self, chapter_id: str) -> ChapterAssemblyPacket:
    packet = ChapterAssemblyPacket(...)
    
    # 加载作者笔记（优先级最高）
    author_note = self._load_author_note(chapter_id)
    if author_note:
        # 放到 packet 的最前面，优先级高于 author_intent 和 creative_focus
        packet.author_note = author_note
        # 扩展规则注入
        packet.expansion_rules = self._build_expansion_rules(author_note)
    
    # 其余模块正常组装...
    return packet

def _load_author_note(self, chapter_id: str) -> str:
    """加载章节作者笔记"""
    note_path = self.src_root / "chapter_notes" / f"{chapter_id}_note.md"
    if note_path.exists():
        return note_path.read_text(encoding="utf-8")
    return ""
```

### 1.3 完整流程示意

```
┌─────────────────────────────────────────────────────┐
│                    青灯规划阶段                       │
│                                                     │
│  大纲确定 → 作者笔记（可选）→ 保存到 chapter_notes/   │
│                                                     │
│                    ↓ Handoff                         │
│                                                     │
│                    落笔写作阶段                       │
│  ┌──────────────────────────────────────────────┐   │
│  │          Canonical Packet 组装                │   │
│  │                                              │   │
│  │  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ ← 检测到     │   │
│  │  ┃ 📝 作者笔记 (当前章)       ┃   笔记存在     │   │
│  │  ┃   优先级: 最高             ┃               │   │
│  │  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛               │   │
│  │                                              │   │
│  │  大纲窗口 (outline window)                    │   │
│  │  人物状态 (character state)                   │   │
│  │  世界规则 (world rules)                       │   │
│  │  风格合成 (composed style)                    │   │
│  │  作者人设 (author persona)                    │   │
│  │  章节记忆 (chapter memory)                    │   │
│  │  ...                                         │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│                    ↓                                 │
│                                                     │
│               Phase 1: 创意写作                       │
│          AI 严格遵循作者笔记扩展正文                   │
│                                                     │
│               Phase 2: 审查+结算                      │
│                                                     │
│                    ↓                                 │
│                                                     │
│              人类确认: "这是我想要的"                  │
└─────────────────────────────────────────────────────┘
```

---

## 二、作者笔记格式规范

### 2.1 完整格式模板

```markdown
# 作者笔记 — ch_XXX

## 本章想要的感觉
（一段话描述本章的情感调色盘。不是写作指令，而是给 AI 的感觉约束。）

## 必须出现的场景
（清单。至少 1 个，建议 3-5 个。每个场景应足够具体——AI 就是把它们连起来。）

## 想尝试的东西
（可选。实验中——可能会失败。AI 可以自由探索，但不能违背上面的约束。）

## 绝不要的
（清单。比"想要的感觉"更硬——AI 绝对不能做的事。）
```

### 2.2 详细示例

#### 示例 1: 一场雨中离别

```markdown
# 作者笔记 — ch_037_雨中渡口

## 本章想要的感觉
一场雨中的离别。不需要煽情，但要让人心里堵得慌。
——那种"明明什么都没说，却好像把一辈子都说完了"的感觉。

## 必须出现的场景
- 林月在渡口等到最后一个人都不是顾恒
- 她没哭，只是把玉佩解下来放在了船板上
- 等船开远了，她才去捡回来——但身体没有动，是蹲下去的时候摔了一跤
- 最后一行字：雨停了，渡口只有一条空船。和一只狗。

## 绝不要的
- 不要任何"回忆杀"闪回（顾恒的样子、过去的对话都别出现）
- 不要让林月说话，全程只靠动作驱动
- 不要描写她的内心活动（"她想""她觉得""她想起"统统不能出现）
- 不要任何形容词形容她的情绪（"悲伤""痛苦""绝望"——都不行）
```

#### 示例 2: 一场大战

```markdown
# 作者笔记 — ch_125_帝都之战

## 本章想要的感觉
一场不是"燃"的战斗。残酷、脏、所有人都害怕。
战斗不是个人表演，是混乱和意外。
读者应该看完这一章后觉得"战争真恶心"，而不是"主角真帅"。

## 必须出现的场景
- 开战三分钟后主角就被打了个措手不及，左臂骨折
- 一个刚刚还和主角并肩作战的配角突然死了——没有铺垫，没有遗言
- 主角在尸体堆里找到了那个人的烟杆，犹豫了一下还是装进怀里
- 结尾：主角意识到这场战斗其实只是佯攻，主力已经绕后了

## 想尝试的东西
- 大量使用断句和碎片化描写来表现战斗的混乱
- 主角的视角间歇性模糊（失血导致的意识游离）

## 绝不要的
- 不要任何"觉醒""爆发"桥段，主角从头到尾被压着打
- 不要反派说废话，反派连名字都没出现
- 不要在战斗中穿插"他想起师父曾经说过..."
- 不要写死前闪回（配角的死要突然、干净、令人发懵）
```

#### 示例 3: 日常过渡章

```markdown
# 作者笔记 — ch_089_客栈夜话

## 本章想要的感觉
暴风雨前的宁静。表面温馨的客栈夜话，底下有无数根绷紧的弦。
——每个人都想说点什么，但每个人都不敢说完。

## 必须出现的场景
- 张三和李四在走廊里偶遇，两人站在微弱的烛光下默数心跳
- 只有一句对话:"她睡了。""嗯。"
- 主角辗转反侧，听到隔壁传来压抑的哭声——他假装没听到

## 绝不要的
- 不要超过 20 句对话
- 不要解释任何人的秘密——每个人都只能说半句话
- 不要让气氛松弛——读者从头到尾要觉得"马上要出事了"
```

### 2.3 格式解析规则

```yaml
# 作者笔记解析配置
author_note_parser:
  
  sections:
    "想要的感觉":
      type: "emotion_constraint"
      injection: "作为风格约束注入 system prompt 的情感基调部分"
      required: true
      max_length: 200  # 中文字符
    
    "必须出现的场景":
      type: "scene_anchor"
      injection: "逐条编入写作指令，标记为「不可省略」"
      required: true
      min_items: 1
      max_items: 10
      preservation_rule: "核心句子原封不动保留到正文中"
    
    "想尝试的东西":
      type: "experimental_hint"
      injection: "作为建议注入，AI 可以自行判断是否可行"
      required: false
      conflict_policy: "与「绝不要的」冲突时，以后者为准"
    
    "绝不要的":
      type: "hard_negative"
      injection: "转化为禁止规则注入 system prompt，优先级最高"
      required: false
      conflict_policy: "与任何其他指令冲突时，以此节为准"

  global_rules:
    priority_chain: "绝不要的 > 必须出现的场景 > 想要的感觉 > 想尝试的东西"
    expansion_ratio: 10  # ~300字草稿 → ~3000字正文
    fallback: "如果笔记缺失，退回标准流程（视为无特殊约束）"
```

---

## 三、AI 扩展规则

### 3.1 规则层级

```
优先级从高到低:
┌────────────────────────────────────────────┐
│ L0: 作者笔记「绝不要的」— 绝对红线            │
├────────────────────────────────────────────┤
│ L1: 作者笔记「必须出现的场景」— 不可省略       │
├────────────────────────────────────────────┤
│ L2: 作者笔记「想要的感觉」— 风格约束          │
├────────────────────────────────────────────┤
│ L3: 创意焦点 (creative_focus) — 阶段方向     │
├────────────────────────────────────────────┤
│ L4: 作者人设 (author persona) — 长期创作人格  │
├────────────────────────────────────────────┤
│ L5: 风格合成 (composed style) — 技法框架     │
├────────────────────────────────────────────┤
│ L6: 作者意图 (author_intent) — 全书底色      │
├────────────────────────────────────────────┤
│ L7: 作者笔记「想尝试的东西」— 实验性建议      │
└────────────────────────────────────────────┘
```

### 3.2 冲突处理

```
核心原则: 作者笔记 > 一切其他约束

具体规则:
  1. 作者笔记「绝不要的」与作者人设语言指纹冲突 → 以笔记为准
  2. 作者笔记「必须出现的场景」与大纲节奏不一致 → 以笔记为准（同时标记警告给作者）
  3. 作者笔记「想要的感觉」与 composed style 冲突 → 以笔记的情绪约束覆盖风格约束
  4. 作者笔记未提及的部分 → 正常使用其他约束层
```

### 3.3 扩展比例控制

```python
# 扩展比例算法
class DraftExpander:
    """人类草稿 → AI 正文扩展器"""
    
    DEFAULT_RATIO = 10  # 默认 10x 扩展
    
    def calculate_expansion_ratio(self, note: AuthorNote) -> float:
        """根据笔记密度计算合适的扩展比例"""
        
        # 场景锚点越多 → 扩展比例越低（因为人类已经给了很多骨肉）
        scene_count = len(note.must_appear_scenes)
        
        if scene_count >= 8:
            return 5.0   # 人类已经写了大部分框架
        elif scene_count >= 5:
            return 7.0   # 中等密度
        elif scene_count >= 3:
            return 10.0  # 标准扩展
        else:
            return 12.0  # 场景少 → 需要 AI 更多填充
    
    def expand(self, note: AuthorNote, target_words: int = 3000) -> str:
        """将作者笔记扩展为目标字数的正文
        
        Returns:
            扩展后的正文文本
        """
        ratio = self.calculate_expansion_ratio(note)
        
        # 核心句子保护: 从「必须出现的场景」中提取需要原封不动保留的句子
        protected_sentences = self._extract_protected_sentences(note)
        
        # 构建扩展 prompt
        system_prompt = self._build_expansion_prompt(
            note=note,
            protected_sentences=protected_sentences,
            ratio=ratio,
        )
        
        # ... 调用 LLM 进行扩展
```

### 3.4 核心句子保护

```python
def _extract_protected_sentences(self, note: AuthorNote) -> List[ProtectedSentence]:
    """从「必须出现的场景」中提取需要原封不动保留的句子
    
    识别规则:
    1. 引号内的完整句子 → 标记为「原文保留」
    2. 特定动作描写（如"把玉佩解下来放在船板上"）→ 标记为「核心动作保留」
    3. 意象/比喻（如"雨停了，渡口只有一条空船"）→ 标记为「意象保留」
    
    Returns:
        带保留标记的句子列表
    """
    protected = []
    
    for scene in note.must_appear_scenes:
        # 提取引号内的对话
        quoted = re.findall(r'"[^"]+"|「[^」]+」', scene.text)
        for q in quoted:
            protected.append(ProtectedSentence(
                text=q.strip('"「」'),
                type="dialogue",
                preservation="verbatim"  # 逐字保留
            ))
        
        # 提取核心动作（动词短语 + 宾语）
        core_actions = self._parse_core_actions(scene.text)
        for action in core_actions:
            protected.append(ProtectedSentence(
                text=action,
                type="core_action",
                preservation="structure"  # 保留动作结构，允许小幅语言包装
            ))
    
    return protected
```

### 3.5 扩展 System Prompt 构建

```python
def _build_expansion_prompt(self, note: AuthorNote, protected_sentences: list, ratio: float) -> str:
    """构建扩展写作的 system prompt"""
    return f"""
## 写作指令（来自作者笔记）

### 硬约束（违者直接拒稿）
{chr(10).join(f"- 绝对禁止: {item}" for item in note.never_do)}

### 必须包含的场景（一个都不能少）
{chr(10).join(f"- 必须包含: {scene.text}" for scene in note.must_appear_scenes)}

### 必须原封不动保留的句子
{chr(10).join(f"- [{s.type}] {s.text} (保留方式: {s.preservation})" for s in protected_sentences)}

### 风格约束
{note.desired_feeling or '（无特殊情绪约束）'}

### 扩展规则
- 作者笔记约 {note.word_count} 字 → 目标正文约 {int(note.word_count * ratio)} 字
- 「逐字保留」句子 → 一模一样出现，不改一个字
- 「结构保留」句子 → 动作不变，允许加环境/心理包装
- 「风格约束」不是文字指令，而是情感调色盘 → 自然渗透，不要直接复述
"""
```

---

## 四、与现有架构的集成

### 4.1 Canonical Packet 中的位置

作者笔记在 canonical packet 中的优先级最高，放在所有其他模块之前：

```python
# models/context_package.py — GenerationContext 新增字段

class GenerationContext(BaseModel):
    # ... 现有字段 ...
    
    # === 新增: 作者笔记 ===
    author_note: str = Field(
        default="",
        description="当前章的作者笔记（优先级最高，来自 src/chapter_notes/）"
    )
    author_note_expansion_rules: str = Field(
        default="",
        description="从作者笔记解析出的 AI 扩展规则"
    )
    
    def to_prompt_context(self) -> str:
        parts = []
        
        # 作者笔记排在最前面 ← 新增
        if self.author_note:
            parts.append(self._render_author_note_section())
        
        # 然后是现有的各模块...
        parts.append(self._render_outline_section())
        parts.append(self._render_character_section())
        # ...
    
    def _render_author_note_section(self) -> str:
        """渲染作者笔记区块"""
        return f"""
## ⚠️ 作者笔记（本章最高优先级约束）

以下内容来自作者手写的创作笔记，优先级高于所有其他约束。

{self.author_note}

{self.author_note_expansion_rules}
"""
```

### 4.2 ChapterAssemblyPacket 中的位置

```python
# chapter_assembler.py — ChapterAssemblyPacket 新增字段

@dataclass
class ChapterAssemblyPacket:
    # ... 现有字段 ...
    
    # === 新增 ===
    author_note: str = ""                    # 作者笔记原文
    expansion_rules: str = ""               # 解析后的扩展规则
    
    def to_markdown(self) -> str:
        parts: List[str] = []
        
        # 作者笔记最前面 ← 新增
        if self.author_note:
            parts.append("## ⚠️ 作者笔记（最高优先级）")
            parts.append(self.author_note)
            parts.append("")
            parts.append("### AI 扩展规则")
            parts.append(self.expansion_rules)
            parts.append("")
        
        # 现有顺序保持不变
        parts.append("## 系统提示词（按职责）")
        parts.append("## 作者意图")
        # ...
```

### 4.3 ContextBuilder 中集成

```python
# context_builder.py — build_generation_context() 新增步骤

def build_generation_context(self, chapter_id: str, window_size: int = 5) -> GenerationContext:
    # ... 现有 1-7 步 ...
    
    # === 新增: 步骤 0 — 加载作者笔记（最先加载，优先级最高） ===
    author_note = self._load_author_note(chapter_id)
    expansion_rules = ""
    if author_note:
        parsed = self._parse_author_note(author_note)
        expansion_rules = self._build_expansion_rules(parsed)
    
    # 构建 context 时传入
    context = GenerationContext(
        # ... 现有字段 ...
        author_note=author_note,
        author_note_expansion_rules=expansion_rules,
    )
    
    return context
```

### 4.4 预算分配调整

引入作者笔记后需要从「弹性缓冲」中预留约 2%（~2500 tokens），作者笔记本身很短（500 tokens 以内），实际净消耗极小。

---

## 五、版本管理

### 5.1 文件结构

```
src/
├── chapter_notes/                  # 作者笔记目录
│   ├── ch_001_note.md              # 与章节一一对应
│   ├── ch_002_note.md
│   ├── ch_003_note.md
│   └── ...
│
├── story/
│   ├── author_intent.md            # 全书长期意图（已有）
│   └── current_focus.md            # 当前阶段创作罗盘（已有）
│
├── outline.md                      # 大纲
└── characters/                     # 角色档案
```

### 5.2 笔记与章节的绑定

```python
# 笔记文件命名约定
NOTE_NAMING_PATTERN = "{chapter_id}_note.md"

# 示例
# 章节: ch_037 → 笔记: src/chapter_notes/ch_037_note.md
# 章节: ch_125 → 笔记: src/chapter_notes/ch_125_note.md
```

### 5.3 笔记的提交单元

作者笔记与对应章节一起构成一个不可拆分的提交单元：

```python
# 伪代码: 提交单元定义
@dataclass
class CommitUnit:
    """一个完整的提交单元"""
    chapter_id: str
    required_files: List[str] = field(default_factory=list)
    optional_files: List[str] = field(default_factory=list)
    
    @classmethod
    def for_chapter(cls, novel_root: Path, chapter_id: str) -> 'CommitUnit':
        return cls(
            chapter_id=chapter_id,
            required_files=[
                f"src/outline.md",                           # 大纲变更
                f"src/chapter_notes/{chapter_id}_note.md",   # 作者笔记
                f"data/manuscript/{chapter_id}.md",          # 正文
                f"data/memory/chapters/{chapter_id}_memory.json",  # 记忆
            ],
            optional_files=[
                f"src/characters/*.md",                      # 角色更新
                f"data/truth/active/deltas/{chapter_id}_delta.yaml",  # 状态更新
            ]
        )
```

### 5.4 笔记缺失的降级行为

```python
def get_expansion_mode(self, chapter_id: str) -> str:
    """判断当前章的写作模式"""
    note_path = self.src_root / "chapter_notes" / f"{chapter_id}_note.md"
    
    if note_path.exists():
        note = self._parse_author_note(note_path.read_text())
        if note.has_must_appear_scenes and note.has_desired_feeling:
            return "human_first"      # 完整人类第一稿模式
        elif note.has_must_appear_scenes:
            return "scene_guided"     # 只有场景锚点
        else:
            return "emotion_guided"   # 只有情绪约束
    else:
        return "standard"             # 无笔记，标准 AI 自由模式
```

### 5.5 笔记的质量检查

```yaml
# 青灯在保存笔记前自动执行的检查
author_note_quality_check:
  required:
    - field: "想要的感觉"
      check: "非空，且不是泛泛的'热血''悲伤'等单字"
      hint: "请描述一种具体的情绪质感，比如'那种明明赢了却觉得输了的感觉'"
    
    - field: "必须出现的场景"
      check: "至少包含 1 条具体的场景描述（有角色、有动作、有画面感）"
      hint: "不要写'主角大战反派'，要写'主角在断桥上被反派一拳打穿左肩，跪在雨中抬头笑'"
  
  warnings:
    - field: "绝不要的"
      check: "如果为空，AI 将不受额外限制"
    
    - field: "想尝试的东西"
      check: "如果为空，AI 不会主动做任何实验"

  rejection:
    - "笔记中出现了'随便写'、'你看着办'、'自由发挥' → 拒绝保存，要求作者写具体"
    - "笔记超过 1000 字 → 建议缩减（太长的笔记 = 作者自己在写正文，不需要 AI 扩展）"
```

---

## 六、完整示例: 端到端流程

### 场景: 作者要通过作者笔记写一章

#### Step 1: 青灯规划阶段

```
青灯: "第 37 章的大纲确定了——林月离开渡口。要不要为本章写一份作者笔记？"
作者: "要。"
青灯: "你想让这章有什么感觉？"
作者: [输入笔记内容]
```

作者笔记内容:

```markdown
# 作者笔记 — ch_037

## 本章想要的感觉
一场失败的等待。读者全程知道顾恒不会来，但林月不知道。
——那种"观众比角色更痛"的视角差。

## 必须出现的场景
- 林月到渡口的时候天还没亮
- 她坐在船板上等了一整天——用"影子从西转到东"来表现时间流逝
- 最后一班船开走的时候，她站起来想喊，但没喊出声
- 她把玉佩解下来放在船板上，转身走了
- 走了十几步，站住。没回头。继续走。

## 绝不要的
- 不要写顾恒为什么没来——那在后面章节才揭晓
- 不要任何对白，林月全程不说话
- 不要写任何路人的同情表情——这个世界不关心她
```

#### Step 2: 落笔写作阶段

落笔的 canonical packet 顶部出现:

```
## ⚠️ 作者笔记（本章最高优先级约束）

...（上述笔记内容）...

### AI 扩展规则
- 硬约束（违者直接拒稿）:
  - 不要写顾恒为什么没来
  - 不要任何对白
  - 不要路人的同情表情

- 必须包含（一个都不能少）:
  - 林月到渡口时天还没亮
  - 用影子从西转到东表现时间流逝
  - 最后一班船开走时想喊没喊出声 ← 核心动作保留
  - 把玉佩解下来放在船板上 ← 核心动作原封保留
  - 走了十几步，站住，没回头，继续走 ← 动作序列原封保留

- 风格约束:
  观众比角色更痛的视角差——全程保持外部视角，不进入林月内心

- 扩展比例: 10x (~300字 → ~3000字)
```

#### Step 3: AI 输出正文（节选）

> 到了渡口的时候，天还没亮。
>
> 河面上的雾气浓得像一碗冷掉的粥，看什么都朦朦胧胧的。码头上已经排了一条船，艄公蹲在船头抽旱烟。林月看了他一眼，走到最靠外的那条空船上，在船板上坐了下来。
>
> 她把包袱放在腿边，两只手搁在膝盖上，像庙里一尊旧了的小菩萨。
>
> 艄公问她去哪儿。
>
> 她说，等人。
>
> 艄公就没再问了。这个渡口每天都有人在等人。
>
> ...（AI 扩展了「影子从西转东」的时间流逝描写）...
>
> 影子从船板的西头爬到东头的时候，最后一只候鸟也飞过去了。
>
> 最后一班船开走的时候，林月突然站起来。嘴张了张。喉咙里像堵了一块冰。
>
> 她没喊出来。
>
> ...（AI 继续扩展至约 3000 字）...
>
> 林月走了十几步。
>
> 站住。
>
> 没回头。
>
> 继续走。

> **作者读完反馈**: "就是我要的。过。"

---

## 七、实施要点

### 7.1 需要修改的文件

| 文件 | 改动内容 | 优先级 |
|------|----------|--------|
| `models/context_package.py` | GenerationContext 新增 `author_note` 和 `expansion_rules` 字段 | P0 |
| `tools/context_builder.py` | 新增 `_load_author_note()` 和 `_parse_author_note()` 方法 | P0 |
| `tools/chapter_assembler.py` | ChapterAssemblyPacket 新增字段，`assemble()` 中加载笔记 | P0 |
| `tools/agent/writer.py` | creative_write 的 system prompt 中加入作者笔记约束 | P0 |
| `skills/qingdeng-agent/SKILL.md` | 青灯子技能中加入「创建作者笔记」流程 | P1 |

### 7.2 不破坏现有流程

```
兼容性设计:
  - 作者笔记是"可选增强"，不改变现有写章流程的核心逻辑
  - 如果没有笔记文件 → 完全退回到当前标准流程
  - 有笔记文件但没有某些节（如没有"绝不要的"）→ 只应用有内容的约束
  - 所有现有字段和流程保持不变
```

---

> *"好的工具不应该替代人类的创造过程，而是放大它。"*
> *—— 人类第一稿设计原则*
