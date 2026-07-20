# 燃灯 — 读者社区模拟器

> 设计日期: 2026-07-19 | 目标: 书还没发，AI 模拟 100 个读者的讨论与反应 | 优先级: P2

---

## 问题定义

小说写完了就发？你知道读者会怎么讨论这一章吗？读者看到的"伏笔"可能和你设计的不一样，读者嗑的 CP 可能和你写的不一致，读者愤怒的点你完全没预料。

**读者社区模拟器不是市场调研——是读者的"毒性测试"。**

```
它能回答的问题:
- 读者看到第 50 章会怎么讨论？这个情节合理还是强行？
- 我埋的伏笔，读者 get 到了吗？他们现在的最大误解是什么？
- 这一章发出去，最可能劝退的是哪类读者？
```

---

## 一、四类模拟读者（各 25 人）

```yaml
# config/reader-simulator.yaml
reader_types:

  warrior:       # 热血少年
    count: 25
    personas:
      - name: "爆裂打工人"
        style: "下班看小说解压，只看打斗和升级"
        keywords: [战力, boss, 突破, 吊打, 碾压]
        catchphrases: ["这章打斗写得爽！", "什么时候突破元婴？"]
        hot_buttons: [战力被压制, 升级太慢]
      - name: "数据党"
        style: "做战力排行表"
        keywords: [境界, 战力对比, 体系矛盾]
        catchphrases: ["第87章说元婴只能打三个化神？那第200章…"]
        hot_buttons: [设定矛盾, 战力破格]
      - name: "最终boss党"
        style: "推理幕后黑手"
        keywords: [幕后黑手, 最终boss, 隐藏大佬]
        catchphrases: ["我感觉幕后是沈流云"]
        hot_buttons: [主角太顺, boss太弱]

  shipper:       # CP党
    count: 25
    personas:
      - name: "官配守护者"
        style: "站定林月×顾恒"
        keywords: [发糖, 虐, 互动, 双箭头]
        catchphrases: ["啊啊啊啊本章有糖！", "求别虐"]
        hot_buttons: [官配被拆, 感情线搁置, 三角关系]
      - name: "邪教领袖"
        style: "嗑冷门CP"
        keywords: [白旭×林月, 火花, 微妙]
        catchphrases: ["没有人觉得白旭和林月火花更强吗"]
        hot_buttons: [冷门被弃, 官配太甜]
      - name: "感情线分析师"
        style: "量化感情进度"
        keywords: [暧昧期, 表白时机, 误会]
        catchphrases: ["本卷感情线推进了3%", "又误会了，第几次了"]
        hot_buttons: [为虐而虐, 误会太刻意]

  analyst:       # 分析党
    count: 25
    personas:
      - name: "时间线警察"
        style: "做大事记年表"
        keywords: [时间线, bug, 矛盾]
        catchphrases: ["这里时间对不上", "第300章说三年，第500章又说五年"]
        hot_buttons: [时间bug, 年龄矛盾]
      - name: "世界观学家"
        style: "分析世界设定"
        keywords: [设定, 体系, 力量层次]
        catchphrases: ["修炼体系是炼气→筑基→金丹→元婴→化神？和传统有啥区别"]
        hot_buttons: [设定被打破, 新规则随机出现]
      - name: "伏笔猎手"
        style: "挖伏笔做理论"
        keywords: [伏笔, 暗示, flag, 铺垫]
        catchphrases: ["第87章的玉佩肯定是个大伏笔", "这个台词是flag"]
        hot_buttons: [伏笔回收太简单, 情节太好猜]

  casual:        # 路人读者
    count: 25
    personas:
      - name: "爽就完了"
        style: "凭感觉"
        keywords: [好看, 弃了, 水, 节奏]
        catchphrases: ["这章有点水", "养了50章了", "弃了"]
        hot_buttons: [节奏太慢, 连续无聊]
      - name: "潜水党"
        style: "从不发言"
        keywords: []
        catchphrases: ["（沉默追读）", "（弃文）"]
        hot_buttons: []
      - name: "梗王"
        style: "造梗截表情包"
        keywords: [名场面, 表情包]
        catchphrases: ["新表情包已做", "哈哈哈哈哈"]
        hot_buttons: [没有爆梗]
```

---

## 二、模拟引擎

```python
# reader_simulator.py
from dataclasses import dataclass, field
from typing import List, Dict
import random

@dataclass
class ReaderPersona:
    name: str; group: str
    style: str; keywords: List[str]
    catchphrases: List[str]; hot_buttons: List[str]
    memory: List[str] = field(default_factory=list)

@dataclass
class DiscussionThread:
    title: str; author: str
    type: str        # analysis | spoiler | rant | theory | funny
    content: str
    replies: List[Dict] = field(default_factory=list)
    likes: int = 0

class ReaderCommunity:
    def __init__(self):
        self.readers: List[ReaderPersona] = []
        self.chapters: List[str] = []
        self.threads: List[DiscussionThread] = []
    
    def load_personas(self, cfg: dict):
        for group, pconfigs in cfg.items():
            for pc in pconfigs['personas'] if isinstance(pconfigs, dict) else []:
                self.readers.append(ReaderPersona(**pc, group=group))
    
    def read_chapter(self, summary: str, ch: int):
        self.chapters.append(f"第{ch}章: {summary[:100]}")
        for r in self.readers: r.memory.append(self.chapters[-1])
    
    def discuss(self, ch: int) -> List[DiscussionThread]:
        threads = []
        for r in self.readers:
            if r.name == "潜水党" and random.random() > 0.15: continue
            t = self._mk_thread(r, ch)
            if t: threads.append(t)
        self._gen_replies(threads[:5])
        return threads
    
    def _mk_thread(self, r: ReaderPersona, ch: int):
        if r.group == "warrior" and random.random() < 0.4:
            return DiscussionThread(f"第{ch}章战力分析", r.name, "analysis",
                f"第{ch}章这个打法...主角现在的境界打这个boss...")
        if r.group == "shipper" and random.random() < 0.35:
            return DiscussionThread(f"第{ch}章糖点合集！", r.name, "spoiler",
                f"本章林月跟顾恒的互动...我死了")
        if r.group == "analyst" and random.random() < 0.45:
            prev = max(1, ch-200)
            return DiscussionThread(f"第{ch}章的一个疑问", r.name, "theory",
                f"第{ch}章提到...但第{prev}章说过...")
        if r.group == "casual" and random.random() < 0.25:
            return DiscussionThread(f"第{ch}章观感", r.name, "rant",
                random.choice(["这章还可以", "有点水", "养肥了再看", "好看！"]))
        return None
    
    def _gen_replies(self, threads: List[DiscussionThread]):
        for t in threads:
            for _ in range(random.randint(1, 8)):
                replier = random.choice(self.readers)
                t.replies.append({"author": replier.name,
                    "content": random.choice(replier.catchphrases),
                    "likes": random.randint(0, 20)})
    
    def consensus(self) -> dict:
        pos, neg = 0, 0
        for t in self.threads:
            if any(w in t.content for w in ["好看","爽","嗑","精彩"]): pos += 1
            elif any(w in t.content for w in ["水","弃","bug","矛盾","无聊"]): neg += 1
        return {"total": len(self.threads), "positive": pos, "negative": neg}
```

---

## 三、输出格式

### 模拟读者讨论报告（节选）

```markdown
# 📢 模拟读者讨论报告 — 第 50 章「断臂」
样本: 100 人 | 讨论帖: 18

## 总体情绪
😃 积极: 42% | 😐 中立: 35% | 😡 负面: 23%

## 🔥 热帖排行榜

### 🥇 战力分析贴 — By 爆裂打工人
🔥 回复 24 | 👍 89
> "顾恒断臂后战力掉了一截。化神中期少右臂还能打同级吗？柳如烟一战我觉着强行。"

回复:
- 数据党: "化神期肉身修复快，一个月恢复7成"
- 最终boss党: "第25章说断肢重生需要天材地宝"

### 🥇 CP帖 — 同框预警 By 官配守护者
🔥 回复 18 | 👍 72
> "从卷4结尾到卷5第3章，林月和顾恒一次同框都没有。作者你在干嘛😭"

回复:
- 感情线分析师: "已连续18章无同框，创全书记录"
- 邪教领袖: "林月跟白旭的戏份反而多了..."

### 🥇 伏笔帖 — 第50章跟第3章有关？By 伏笔猎手
🔥 回复 12 | 👍 65
> "第3章说顾恒手腕有'一道极浅的旧疤'。化神强者为什么会有旧疤？"

回复:
- 世界观学家: "化神期不能有疤没有提到"
- 时间线警察: "旧疤是'很多年前'的，第50章是现在断的，对不上"

## ⚠️ 读者误解清单
1. 🟡 **断臂战力大幅下降** → 实际安排了左手剑外挂
   → 建议: 第52-54章插入顾恒展示左手剑天赋

2. 🟡 **林月和白旭有感情线** → 实际林月心系顾恒
   → 建议: 第51章安排林月独白锚定心理归属

3. 🔴 **第3章旧疤和第50章断臂有关** → 实际无关
   → 建议: 如无关不要强化联想；如有关尽快揭示

## 📊 读者细分情绪
| 类型 | 情绪 | 主要关注 |
|------|------|---------|
| 热血少年 | 🟡 中立 | 战力不崩就行 |
| CP党 | 🔴 焦虑 | 同框太少，怕拆CP |
| 分析党 | 🟢 兴奋 | 找到了新素材 |
| 路人读者 | 🟡 中立 | 还行，不到弃的程度 |

## 建议行动
1. **立即**: 2章内安排顾恒展示左手剑（安抚热血少年）
2. **紧急**: 1章内给林月一个心理锚定（安抚CP党）
3. **可选**: 确认第3章旧疤是否要关联（误导变伏笔）
```

---

## 四、实用场景与集成

### 预检场景

| 场景 | 问题 | 频率 |
|------|------|------|
| 主角获得新外挂 | 路人觉着太强，数据党觉着合理 | ⟳ |
| 引入新女主角 | CP党分裂，路人无所谓 | ⟳ |
| 节奏变慢（铺垫卷） | 路人大面积弃文，分析党理解 | ⟳ |

### 与 literary-audit 联动

```yaml
audit_dimensions:
  reader_reaction_prediction:
    enabled: true
    min_positive_ratio: 0.3
    max_complaints: 5
    alerts:
      - type: misunderstanding
        severity: high
        action: "建议在 n 章内澄清"
```

### 完整配置

```yaml
# config/reader-simulator.yaml
enabled: true
run_on: pre_release           # 每章发布前
reader_types:
  warrior:  { count: 25 }
  shipper:  { count: 25 }
  analyst:  { count: 25 }
  casual:   { count: 25 }
simulation:
  max_threads_per_chapter: 30
  reply_generation: true
  analyze_misunderstandings: true
output:
  report_path: data/reader-sim/reports/
  notify_on:
    - major_misunderstanding
    - negative_ratio_high
```

---

> *"一本好小说不是只在讲故事——它在为读者创造一个可以争吵的世界。"*
