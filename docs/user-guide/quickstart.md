# 🚀 5 分钟快速开始

> 从安装到写出第一章，只需三步。

---

## 安装

```bash
pip install openwrite
```

> 需要 Python 3.10+。推荐在虚拟环境中安装。

验证安装：

```bash
openwrite --version
# OpenWrite 5.8.0
```

---

## 第一步：配置 AI 模型（30 秒）

燃灯需要连接一个 AI 模型来帮你写作。运行配置向导：

```bash
openwrite setup
```

向导会带你完成：

1. **选择 AI 提供商** — 支持 OpenAI、DeepSeek、智谱(GLM)、Anthropic Claude、SiliconFlow 等
2. **输入 API Key** — 从对应平台获取（向导会给出链接）
3. **选择模型** — 初学者推荐 `gpt-4o-mini`（OpenAI）或 `glm-4-flash`（智谱免费）
4. **测试连接** — 自动验证配置是否可用

```
  ╭─────────────────────────╮
  │      燃  灯  配  置      │
  │    AI 模型连接向导      │
  ╰─────────────────────────╯

  步骤 1: 选择 AI 提供商
     [1] OpenAI
     [2] DeepSeek
     [3] 智谱 (GLM)
     ...

  步骤 2: 输入 API Key
```

> **小贴士：** 智谱 GLM-4-Flash 目前免费，适合新手尝鲜。
> 之后随时运行 `openwrite setup` 可以换模型。

---

## 第二步：创建一本小说（15 秒）

```bash
openwrite init
```

交互式向导会问你几个简单问题：

| 问题 | 示例回答 |
|------|---------|
| 你的小说叫什么名字？ | 仙王的日常 |
| 什么题材？ | 修仙 / 都市 / 科幻 ... |
| 一句话简介？ | 一个被退婚的少年捡到了一块会说话的玉佩…… |

完成后，项目结构是这样的：

```
my-novel/
├── novel_config.yaml         ← 项目配置
├── src/                      ← 你来编辑的源文件
│   ├── outline.md            大纲
│   ├── characters/           角色档案
│   └── world/                世界观设定
└── data/                     ← AI 自动生成的运行时数据
    ├── hierarchy.yaml
    └── manuscript/           手稿正文
```

---

## 第三步：写第一章！（回车即写）

```bash
openwrite write next
```

燃灯会自动：

1. 读取你的大纲和之前的剧情
2. 构建完整的故事上下文
3. 调用 AI 模型生成一章正文
4. 保存到手稿目录

运行后你会看到：

```
正在写章节: ch_001
章节已生成: 第一章 玉佩
字数: 3420
真相文件已更新: current_state, ledger
```

---

## 就这样？

对，就这样。你已经写出了第一章 🎉

后续还可以：

```bash
openwrite write next       # 写第二章
openwrite desk             # 打开小说工作台，看全局进度
openwrite goethe           # 和策划编辑讨论大纲和角色
openwrite review latest    # 审查最新章节
openwrite export           # 导出整本小说
```

---

## 遇到问题？

- `openwrite --help` — 查看所有命令
- 查看 `docs/user-guide/faq.md` — 常见问题
- 查看 `docs/user-guide/concepts.md` — 核心概念说明
