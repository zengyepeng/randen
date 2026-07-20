---
name: randen-novel
description: 'Use when user wants to write novels, manage outlines, characters, world-building, style, workflows, or chapter review. Triggers: 写章节, 生成大纲, 创建角色, 世界观, 风格, 伏笔, 小说, 燃灯, 青灯, 落笔'
---

# 燃灯 — 长篇小说 AI 写作系统

燃灯是你的长篇小说 AI 写作合伙人。两个 Agent 分工协作：青灯规划，落笔写作。

当前口径统一：

- 日常入口只有两个：`randen qingdeng` 与 `randen luobi`
- `src/` 是人和 AI 共读的确认版真源
- `data/` 是运行态、缓存、workflow、手稿与草案
- `src/story/author_intent.md` 是长期作者意图
- `src/story/current_focus.md` 是近期创作罗盘
- 落笔是主编排入口，青灯是长期 planning 入口
- `write` / `multi-write` / `review` 推进同一套 runtime state
- 每章摘要、观察与三阶段 token 用量保存在 `data/memory/chapters/`
- 写章使用跨进程作品锁，正文、truth、memory 做失败回滚

## @quick-reference 缓存优化

写章前系统组装 canonical packet 时，做了分层缓存以降低重复 I/O：

```text
┌─ L1: In-Memory LRU (TTL 300s, max 10 entries)
│  键 = (novel_id, chapter_id) → 完整 canonical packet
│  命中时跳过全部组装流程
├─ L2: 文件变更检测
│  基于 src/ 和 data/ 关键文件的 mtime 聚合哈希
│  核心文件无变化时跳过加载
├─ L3: 逐模块惰性加载
│  大纲、角色、风格、世界观各自独立缓存，按需刷新
└─ 失效策略
    sync_runtime_caches 调用时主动失效
    写章完成后使当前章节缓存过期
```

**AI 辅助写作时：** 首次写章完整组装上下文（~50ms I/O），后续重写同一章直接命中 L1 缓存（<1ms）。切换章节时大纲和世界观缓存仍有效，只刷新章节窗口和出场角色。

**作者改 `src/` 后：** 运行 `randen sync` 触发缓存失效，下次写章全量重建。

## 青灯 / 落笔 分工

- **青灯（Qingdeng）** 负责长会话规划：汇总灵感、提建议、修背景、修人物、修设定、修大纲，并在资产成熟时显式 handoff 给落笔
- **落笔（Luobi）** 负责把可写资产持续写成正文：预检、写章、审查、状态结算；必要时为正文推进回修人物、设定和大纲

**入门记忆：** 脑洞阶段开青灯；开始写了切落笔。不要反过来。

## 子技能导航

根据用户意图，读取对应子技能的 `SKILL.md`：

| 用户意图 | 子技能文件 | 说明 |
|----------|-----------|------|
| 写章节 / 续写 / 生成草稿 | [落笔 Agent](./skills/goethe-agent/SKILL.md) | 章节创作 Pipeline：预检→写作→审查→结算 |
| 审查 / 润色 / 连续性检查 | 同上 | 通过落笔 Agent 统一处理，含 37 维度审计 |
| 角色 / 大纲 / 世界观 / 伏笔管理 | [项目管理](./skills/novel-manager/SKILL.md) | 项目资产维护 |
| 风格初始化 / 合成 / 提取 | [风格系统](./skills/style-system/SKILL.md) | 三级风格：技法→来源→作品 |
| 世界观实体 / 关系图谱 | [世界查询](./skills/world-query/SKILL.md) | 世界查询 |
| 对话风格 / 口头禅分析 | [对话质量](./skills/dialoguequality/SKILL.md) | 对话指纹检测 |
| 真相文件一致性 | [真相验证](./skills/truth-validation/SKILL.md) | 运行态验证 |
| 后置规则检查 | [发布验证](./skills/post-validation/SKILL.md) | AI 痕迹与规则检测 |
| 伏笔 DAG 管理 | [伏笔系统](./skills/foreshadowing-system/SKILL.md) | 伏笔跟踪 |
| 工作流 / 阶段进度 / 恢复 | [流程管理](./skills/workflow-manager/SKILL.md) | 流程调度 |
| 切割 / 压缩 / 长文本处理 | [文本处理](./skills/text-processing/SKILL.md) | 文本处理 |
| 长期规划 / 建书 / 灵感收敛 | [青灯 Agent](./skills/goethe-agent/SKILL.md) | 青灯 planning 会话与 handoff |

> 原 OpenWrite 中 `novel-creator` 和 `novel-reviewer` 子技能已合并到落笔 Agent。章节创作和审查通过落笔统一入口处理，不再单独拆分。

## 章节创作流程

### 写章前：Canonical Packet 组装

```python
from pathlib import Path
from tools.chapter_assembler import ChapterAssemblerV2

assembler = ChapterAssemblerV2(
    project_root=Path.cwd(),
    novel_id="my_novel",
    style_id="my_novel",
)
packet = assembler.assemble("ch_005")
prompt_text = packet.to_markdown()
```

packet 包含：故事背景、历史篇梗概、当前大纲窗口、主角状态、相关人物、风格文档、世界观规则、上一章正文、伏笔状态——一份落笔写章前需要知道的一切。

### 写章：两阶段写作

1. **Phase 1 — 创意写作**（temperature=0.7）：落笔基于 canonical packet 生成正文
2. **Phase 1.5 — 写后验证**（零成本规则检查）：字数、结构、格式
3. **Phase 2a — 观察者**：从本章提取事实（发生了什么、谁做了什么、伏笔进展）
4. **Phase 2b — 结算者**：将事实合并到真相文件
5. **Phase 2.5 — 状态验证**：检查结算后的一致性

### 审查：37 维度审计

写完后落笔自动跑审查，分四层：

| 层级 | 内容 | 成本 |
|------|------|------|
| 规则检查 | 字数、段落等长、列表式结构 | 零成本 |
| AI 痕迹检测 | 套话词库 + 转折模式 + `ai_patterns.yaml` | 零成本 |
| LLM 深度审计 | 37 维度：角色连续性、情节合理性、对话指纹、伏笔状态 | 一次 LLM 调用 |
| 敏感词检查 | 自定义敏感词表 | 零成本 |

审稿结果保存在 `data/reviews/ch_*.json`，分数和问题明细可在灯台中回看。

## 大纲层级

```text
总纲 (Master)
  └─ 篇纲 (Arc)       — 长线篇章，通常 150-300 章量级
      └─ 节纲 (Section) — 中层段落，通常 15-40 章量级
          └─ 章纲 (Chapter) — 最小写作单元，通常 3000-5000 字
```

`src/outline.md` 是唯一语义真源。`data/hierarchy.yaml` 是派生缓存，不应手工维护。

## 风格层次

```text
craft/                                      → 通用写作技法
data/novels/{id}/data/sources/{source_id}/  → 用户提供文本提取出的 source pack
data/novels/{id}/src/**                     → 本书设定约束
data/novels/{id}/data/style/composed.md     → 合成后的作品风格文档
```

一句话记忆：
- `sources/{id}` = 参考文章的拆解笔记
- `manifest.toml` = 整理后的可用风格清单
- `composed.md` = 最终给这本书用的风格说明书

## 运行态目录

`data/novels/{id}/data/` 下的重点目录：

- `planning/`：草案、灵感、未确认大纲
- `manuscript/arc_*/ch_*.md`：章节正文
- `world/`：`current_state.md` / `ledger.md` / `relationships.md`
- `workflows/`：`book_state.yaml` 与 `wf_ch_*.yaml`
- `memory/chapters/`：有界章节摘要、客观观察与 token 用量
- `reviews/`：结构化章节审稿结果
- `foreshadowing/dag.yaml`：伏笔图
- `style/`：`fingerprint.yaml` 与 `composed.md`

## CLI 入口

### 主入口

- `randen luobi`：长期会话主编排入口（日常高频使用）
- `randen qingdeng`：长期会话 planning 入口（脑洞阶段用）
- `randen dengtai`：打开灯台写作工作台
- `randen` / `randen status`：查看作品进度和下一步建议

不再提供 `randen agent`（原 `openwrite agent` 已退役）。

### 直接命令（调试 / 脚本化用）

- `randen write ch_005`
- `randen multi-write ch_005`
- `randen review ch_005`
- `randen context ch_005 --show`
- `randen assemble ch_005 --output-dir out`
- `randen style synthesize`
- `randen setting extract <source_id> --source <file>`
- `randen source review <source_id>`
- `randen source promote <source_id> --target all`
- `randen sync --check` / `randen sync`
- `randen focus set "本阶段目标" --keep "必须保留" --avoid "必须避免"`
- `randen import existing-novel.txt`
- `randen export --format md`

### 约束

- `write` / `multi-write` / `review` 复用 canonical packet 语义
- 直接 CLI 也推进 `book_state.yaml` 与 `wf_ch_*.yaml`
- CLI 与灯台共用同一套写章锁、事务提交、审稿存储和生命周期

## 单源文档规范

### 核心文档格式

使用 `TOML front matter + Markdown 正文`：

```markdown
+++
id = "char_001"
summary = "主角林月，28岁，都市异能者"
tags = ["主角", "异能", "都市"]
detail_refs = ["world/rules.md"]
related = ["char_002"]
+++

# 林月

正文内容……
```

### 创作罗盘

- `src/story/author_intent.md`：整本书长期不变的创作承诺
- `src/story/current_focus.md`：近期写作最高优先级约束

两者都会进入 canonical packet，压住模型跑偏。

## 目录约定

```text
data/novels/{novel_id}/
├── src/
│   ├── outline.md
│   ├── story/*.md
│   ├── characters/*.md
│   └── world/
│       ├── rules.md
│       ├── terminology.md
│       ├── timeline.md
│       └── entities/*.md
└── data/
    ├── hierarchy.yaml
    ├── planning/*.md
    ├── characters/cards/*.yaml
    ├── manuscript/arc_*/ch_*.md
    ├── memory/chapters/ch_*.yaml
    ├── reviews/ch_*.json
    ├── foreshadowing/dag.yaml
    ├── world/*.md
    ├── style/composed.md
    ├── style/fingerprint.yaml
    ├── workflows/book_state.yaml
    ├── workflows/wf_ch_*.yaml
    └── test_outputs/
```

## 核心 Python 工具

| 工具 | 文件 | 用途 |
|------|------|------|
| 大纲解析 | `tools/outline_parser.py` | `outline.md` → `OutlineHierarchy` |
| 上下文构建 | `tools/context_builder.py` | 章节级生成上下文 |
| 章节组装 | `tools/chapter_assembler.py` | canonical packet |
| 主编排器 | `tools/agent/orchestrator.py` | 书级流程推进 |
| 多 Agent 编排 | `tools/agent/director.py` | `multi-write` 子流程 |
| 工作流调度 | `tools/workflow_scheduler.py` | `wf_ch_*.yaml` |
| 真相文件管理 | `tools/truth_manager.py` | runtime truth files |
| 世界查询 | `tools/world_query.py` | 世界观实体与关系 |
| 风格合成 | `tools/style_synthesizer.py` | 三级风格合成 |

## 参考入口

- [README.md](./README.md) — 项目概览与命令入口
- `tests/test_novel_workspace.py` — 小说工作台验收测试

*版本: 1.0.0 | 继承自 OpenWrite 5.8.0 | 最后更新: 2026-07-19*
