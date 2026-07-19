# 燃灯 — 人物声音隔离分析

> 设计日期: 2026-07-19 | 目标: 检测多视角小说中不同角色的"语言指纹"是否可区分 | 优先级: P1

---

## 问题定义

多视角长篇最隐蔽的 bug——**去掉人名，分不清谁在说话**。

100 章以内尚可凭记忆分配独特语气。2000 章后，林月和顾恒开始使用完全相同句式。不是刻意为之，而是长文本的统计回归效应：角色语言向均值坍缩。

**核心假设：角色语言的区分度，是长篇可读性的隐形基石。**

```
症状清单:
□ 两个角色时，谁说了哪句话要回头标注
□ 角色在情绪激动时反而更"一般化愤怒"
□ 同一角色第 100 章和第 500 章的对话风格无差异或差异过大
□ 所有角色的反问/感叹/设问分布几乎一致
```

---

## 一、语言指纹提取

### 1.1 九维特征向量

```python
# voice_fingerprint.py
from dataclasses import dataclass, field
from typing import List, Dict
import re
from collections import Counter

@dataclass
class VoiceFingerprint:
    """角色的语言指纹——九维特征向量"""
    character_name: str
    chapter_range: tuple
    avg_sentence_length: float = 0.0
    sentence_length_std: float = 0.0
    sentence_types: Dict[str, float] = field(default_factory=lambda: {
        "陈述": 0, "反问": 0, "感叹": 0, "设问": 0, "祈使": 0, "省略": 0
    })
    modal_particles: Dict[str, float] = field(default_factory=dict)
    first_person_style: Dict[str, float] = field(default_factory=dict)
    top_verbs: List[str] = field(default_factory=list)
    punctuation_profile: Dict[str, float] = field(default_factory=lambda: {
        "逗号": 0, "感叹号": 0, "问号": 0, "冒号": 0, "破折号": 0
    })
    negation_rate: float = 0.0
    rhetoric_profile: Dict[str, float] = field(default_factory=dict)
    discourse_markers: Dict[str, float] = field(default_factory=dict)
```

### 1.2 提取逻辑

```yaml
# config/voice-isolation.yaml
pipeline:
  extract:
    min_dialogue_length: 4
    speaker_assign:
      method: nearest_speaker_tag
      fallback: paragraph_context
  per_character:
    output_dir: data/voice-isolation/characters/
    sample_size: 200
```

```python
def extract_fingerprint(dialogues):
    sent = []
    for para in dialogues:
        s = re.split(r'[。！？!?]', para)
        sent.extend([x.strip() for x in s if len(x.strip()) > 2])
    lengths = [len(s) for s in sent]
    avg = sum(lengths) / len(lengths) if lengths else 0
    # 语气词提取
    particles = re.findall(r'[了啊吧吗呢呀嘛哦嗯么哈]', ''.join(dialogues))
    modal = dict(Counter(particles).most_common(10))
    return {"avg_sentence_length": avg, "modal_particles": modal}
```

---

## 二、对比与告警规则

```yaml
# config/voice-isolation.yaml (续)
alerts:
  # 规则 1: 角色间语言重合过高
  cross_character_overlap:
    threshold: 0.60                     # Jaccard 词汇重合率
    top_k_words: 200
    action: warning
    sample:
      message: "「{char_a}」与「{char_b}」词汇重合率 {rate:.0%}，超过阈值 60%"
  
  # 规则 2: 角色自身漂移（跨卷对比）
  within_character_drift:
    window_size: 500
    segment_size: 50
    drift_threshold: 0.35               # 余弦距离
    action: notice
    sample:
      message: "「{char}」卷{va}→{vb} 句长从 {old} 字降到 {new} 字——角色弧线还是意外漂移？"
  
  # 规则 3: 所有角色向均值回归
  regression_to_mean:
    check_frequency: per_500_chapters
    min_diversity: 0.40
    action: warning
```

### 角色对比引擎

```python
class VoiceIsolationEngine:
    def __init__(self):
        self.fingerprints = {}     # Dict[str, List[VoiceFingerprint]]
    
    def register(self, name, dialogues):
        fp = extract_fingerprint(dialogues)
        self.fingerprints.setdefault(name, []).append(fp)
    
    def run_diagnostic(self):
        reports = []
        names = list(self.fingerprints.keys())
        # 角色间交叉对比
        for i, a in enumerate(names):
            for b in names[i+1:]:
                fa, fb = self.fingerprints[a][-1], self.fingerprints[b][-1]
                sim = self._jaccard(fa, fb)
                if sim > 0.60:
                    reports.append(f"⚠️ {a} ↔ {b} 重合 {sim:.0%}")
        # 自身漂移
        for name in names:
            fl = self.fingerprints[name]
            if len(fl) >= 2:
                drift = self._cosine_dist(fl[-1], fl[-2])
                if drift > 0.35:
                    reports.append(f"⚠️ {name} 自身漂移 {drift:.2f}")
        return reports
    
    def _jaccard(self, a, b):
        wa = set(a.top_verbs) | set(a.modal_particles.keys())
        wb = set(b.top_verbs) | set(b.modal_particles.keys())
        return len(wa & wb) / len(wa | wb) if (wa and wb) else 0
```

---

## 三、输出格式

### 人物声音独立性报告（节选）

```markdown
# ⚠️ 人物声音独立性报告 — 卷 5

## 概览

| 角色 | 独立性评分 | 变化趋势 |
|------|-----------|---------|
| 林月 | 87/100 | → 稳定 🟢 |
| 顾恒 | 82/100 | ↑ 改善 🟢 |
| 白旭 | 74/100 | ↓ 下降 🟡 |
| 苏晴 | 53/100 | ↓↓ 恶化 🔴 |

### 🔴 苏晴 (53/100)

**问题：苏晴与林月语气词 Top 5 完全相同（啊/吧/呢/吗/了），句长分布几乎一致（12.3字±4.1 vs 12.1字±3.9）**

建议：苏晴最初人设是"话少但犀利"。让她多用省略号和反问，减少"啊""吧"等软化语气词。

### 🟡 白旭 (74/100)

句长从卷1的18.5字降到卷5的11.8字，主语省略率从23%上升到41%。
这是角色弧线（从游刃有余→心事重重）还是意外漂移？建议在 author-notes 确认。
```

---

## 四、集成方案

### 触发时机

```
写入阶段: 每章 → 增量更新角色指纹
审计阶段: 每200章 → 完整诊断报告
回溯阶段: 首次上线 → 全量基线；修改后 → 重算指纹
```

### 与 literary-audit 联动

```yaml
# literary-audit 集成 fork
audit_dimensions:
  dialogue_quality:
    sub_checks:
      - voice_isolation:
          report_path: data/voice-isolation/reports/latest.md
          weight: 3.0
          min_score: 60
```

### 完整配置

```yaml
# config/voice-isolation.yaml
enabled: true
run_on: cron
cron_schedule: "0 4 * * 0"
characters:
  core: [林月, 顾恒, 白旭, 赵墨, 苏晴, 沈流云]
  secondary: [陈玄, 柳如烟, 秦川]
pipeline:
  min_dialogue_length: 4
  samples_per_character: 200
alerts:
  cross_character_overlap: { threshold: 0.60, action: warning }
  within_character_drift: { threshold: 0.35, action: notice }
  regression_to_mean: { min_diversity: 0.40, action: warning }
output:
  report_path: data/voice-isolation/reports/
  auto_fix: false
```

---

> *"一个好作者，不只是在写故事——他在给每个角色造一张嘴。"*
