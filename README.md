<p align="center">
  <h1 align="center">🏮 燃灯</h1>
  <h3 align="center">你的长篇小说 AI 写作合伙人</h3>
</p>

<p align="center">
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/version-1.0.0-eab308" alt="Version"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-%3E%3D3.10-22c55e" alt="Python >= 3.10"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0891b2" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/entry-randen%20luobi-0f172a" alt="Primary Entry: randen luobi">
</p>

<p align="center">
  <em><strong>燃灯一盏，故事自成。</strong></em>
</p>

---

## 为什么你需要燃灯

你有一个故事。它在你脑子里活了很久——主角的眼神、世界的规则、那个注定要发生的转折。你知道它值得被写下来。

但你试过：

- **裸写 ChatGPT**：聊到第 20 章，它忘了第 3 章埋的伏笔。你不得不重新解释世界观，像是跟一个失忆的搭档合作。
- **大纲写到后面忘了前面**：50 章的角色突然消失，因为大纲太长了，你自己都懒得往回翻。
- **AI 写作一眼假**：句句都是"他微微一笑""他的眼中闪过一丝复杂的情绪"，读起来像 GPT 套 GPT。
- **审稿靠感觉**：重读几十万字找前后矛盾——你宁愿再写一本新的。

<p align="center">
  <strong>这不是又一个 AI 写作工具。这是坐在你旁边的合伙人。</strong>
</p>

## 燃灯怎么解决

燃灯不代替你写作。它做人类作者最累的那些事：记住一切、保持连续、提醒你哪里不对。

### 🔦 双 Agent 协作——青灯规划，落笔写作

| | 青灯（Qingdeng） | 落笔（Luobi） |
|---|---|---|
| **职责** | 灵感整理、人物设定、世界观、大纲规划 | 章节写作、质量审查、状态结算 |
| **比喻** | 深夜灯下翻笔记的那个你 | 提笔就写、写完还自己审的那个你 |
| **入口** | `randen qingdeng` | `randen luobi` |
| **何时用** | 脑洞阶段、修大纲、整理设定 | 日常推进正文 |

青灯帮你把零散的灵感整理成"可写资产"，然后显式交接给落笔。落笔接手后，一章一章往前推，同时维护世界状态——哪个人物在哪一章做了什么，还剩多少伏笔没回收。

### 📦 Canonical Packet——每章都看到完整地图

写第六章的时候，落笔看到的不是"请写第六章"这么简单。它拿到的是一个完整的上下文包：

```text
┌─ 当前大纲窗口（上一篇/本篇/节/章大纲）
├─ 出场角色（人物档案 + 当前状态）
├─ 伏笔 DAG（谁埋了什么、该回收什么）
├─ 三层风格合成（技法 + 来源 + 作品约束）
├─ 世界观规则
├─ 真相文件（资源账本 / 人物关系 / 当前状态）
├─ 上一章正文 + 近期章节记忆
└─ 创作罗盘（作者意图 + 当前焦点）
```

一百章后，它还是记得第一百章开头的那个伏笔。

### 🛡️ 37 维度审查——AI 看不出是 AI 写的

写完后不是直接交稿。落笔会跑一遍自动审查：

- **规则层**：字数达标？段落过短？列表式结构太多？
- **AI 痕迹检测**：套话词库 + 转折模式 + 可配置的 `ai_patterns.yaml`
- **LLM 深度审计**：角色连续性、情节合理性、对话指纹一致性、伏笔状态
- **敏感词检查**：可自定义的敏感词表

审完后你可以直接审报告看分数和问题明细，而不是逐字重读。

### 🗂️ 单一真源——你只改一个地方

`src/` 是人和 AI 共读的确认版。`data/` 是运行态和缓存。你只改 `src/`，系统自动刷新派生数据。

不要再打开三个文档同步同一个人物描述了。

### 🔒 跨进程写章锁 + 快照回滚

写章失败不会留下半章或半份状态。正文、真相文件、章节记忆作为一个原子事务提交——任一步失败，自动恢复到写前快照。

## 不是 NovelAI，不是笔灵 AI

| | 燃灯 | NovelAI | 裸写 ChatGPT |
|---|---|---|---|
| **定位** | 长篇 AI 合伙人 | 英文 AI 写作 | 通用对话 |
| **中文长篇** | ✅ 原生设计 | ❌ 不支撑 | ❌ 上下文窗口不够 |
| **大纲层级** | 总纲→篇→节→章 四层 | 无 | 自己管理 |
| **角色连续性** | 自动追踪 + 状态结算 | 无 | 手动 prompt |
| **伏笔管理** | DAG 图 + 状态统计 | 无 | 无 |
| **AI 痕迹检测** | 37 维审查 + 套话词库 | 无 | 无 |
| **原子写章** | 锁 + 快照 + 回滚 | 无 | 无 |
| **风格合成** | 技法→来源→作品 三层 | 基础风格 | 靠 prompt |
| **创作罗盘** | 作者意图 + 当前焦点 | 无 | 无 |
| **整书导出** | Markdown / TXT | 有限 | 手动复制 |

笔灵 AI 做短文和文案，燃灯只做一件事：**帮人写完长篇小说。**

## 快速开始

### 1. 安装

```bash
git clone https://github.com/LiPu-jpg/randen.git
cd randen
python3.10 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. 配置模型

```bash
export LLM_API_KEY=your-key
export LLM_MODEL=glm-5
```

### 3. 开始写你的第一本小说

```bash
# 第一步：让青灯帮你整理脑洞
randen qingdeng

# 第二步：设定成熟后，落笔开写
randen luobi

# 第三步：打开灯台，看着它推进
randen dengtai
```

就这样。三行命令，开始你和小说的真正相处。

## 项目架构

```text
┌─────────────────────────────────────────────────────────┐
│                    用户入口                              │
│   CLI (randen)  │  灯台 Studio  │  青灯  │  落笔        │
└──────────────────────┬──────────────────────────────────┘
                       │
       ┌───────────────▼────────────────┐
       │      小说应用服务层               │
       │   NovelApplicationService       │
       ├─────────────────────────────────┤
       │  ├─ canonical packet 组装        │
       │  ├─ 章节写作管线                  │
       │  ├─ 37 维审查                    │
       │  ├─ 来源提取 / 晋升               │
       │  └─ workflow / truth / memory    │
       └───────────────┬────────────────┘
                       │
       ┌───────────────▼────────────────┐
       │         核⼼引擎                 │
       ├─────────────────────────────────┤
       │  编排器     │  青灯 Agent         │
       │  落笔 Agent │  审查 Agent         │
       │  ReAct 循环 │  Writer/Director   │
       └───────────────┬────────────────┘
                       │
       ┌───────────────▼────────────────┐
       │         数据层                   │
       ├─────────────────────────────────┤
       │  src/ (真源)  │  data/ (运行态)   │
       │  大纲·人物·世界│  手稿·真相·记忆    │
       └─────────────────────────────────┘
```

## 目录结构

```text
data/novels/{novel_id}/
├── src/                        # 人和 AI 共读的确认版真源
│   ├── outline.md              # 唯一大纲真源
│   ├── story/                  # 作者意图 / 背景 / 基础设定
│   ├── characters/*.md         # 人物正典
│   └── world/                  # 世界观规则 / 术语 / 时间线 / 实体
└── data/                       # 运行态与缓存
    ├── planning/               # 草案与灵感
    ├── manuscript/             # 章节正文（arc_*/ch_*.md）
    ├── world/                  # current_state / ledger / relationships
    ├── memory/chapters/        # 有界章节记忆
    ├── foreshadowing/dag.yaml  # 伏笔图
    ├── style/                  # 合成风格文档
    ├── workflows/              # book_state + 章节 workflow
    └── reviews/                # 结构化审稿结果
```

## 常用命令速查

| 你要做什么 | 命令 |
|---|---|
| 整理脑洞、规划设定 | `randen qingdeng` |
| 日常推进正文 | `randen luobi` |
| 打开写作工作台 | `randen dengtai` |
| 查看进度 | `randen status` |
| 强制写指定章节 | `randen write ch_006` |
| 审查已写章节 | `randen review ch_006` |
| 查看上下文组装 | `randen context ch_006 --show` |
| 设置创作罗盘 | `randen focus set "本阶段目标"` |
| 导入旧稿 | `randen import book.txt` |
| 整书导出 | `randen export --format md` |

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `LLM_API_KEY` | 模型 API Key | 无 |
| `LLM_MODEL` | 模型名 | `gpt-4o-mini` |
| `LLM_BASE_URL` | 自定义兼容网关 | `https://api.openai.com/v1` |
| `LLM_TEMPERATURE` | 默认温度 | `0.7` |
| `LLM_MAX_TOKENS` | 最大输出 token | `24000` |

## 开发者

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码检查
ruff check .
mypy tools/
```

## 许可

MIT License · 开源

---

<p align="center">
  <em>夜深人静，燃灯一盏。<br>墨香氤氲间，故事徐徐展开。</em>
</p>

<p align="center">
  <sub>燃灯 (Randen) 继承自 <a href="https://github.com/LiPu-jpg/Openwrite">OpenWrite</a> 项目，向其作者致敬。</sub>
</p>
