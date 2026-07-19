# ❓ 常见问题

---

## 入门

### Q: 和直接让 ChatGPT 写有什么区别？

**A:** 最大的区别是：**燃灯有记忆。**

ChatGPT 每次对话都是新的开始。写到第 30 章，它已经忘了第 3 章发生了什么——主角在那章突破筑基了，但第 30 章它可能又写了一遍突破筑基。

燃灯不一样：

- 它有 **真相档案**，记录了已经发生的一切
- 它有 **伏笔系统**，第 5 章埋的伏笔，第 50 章会自动提醒你回收
- 它有 **风格指纹**，确保第 1 章和第 100 章读起来像同一个人写的

一句话：ChatGPT 写的是一个个片段，燃灯写的是一整本书。

---

### Q: 需要联网吗？

**A:** 需要联网才能调用 AI 模型。但你的书稿存在本地。

你写的每章正文都保存在你电脑上：

```
data/novels/你的小说名/data/manuscript/
```

即使断网，你的稿子不会丢。要写新章节才需要联网调用 AI。

---

### Q: 免费吗？

**A:** 燃灯的代码完全开源免费。但 AI 模型调用需要按你的 API provider 付费。

费用参考：

| 提供商 | 模型 | 费用（输出） | 写 10 万字大约 |
|--------|------|-------------|---------------|
| 智谱 | GLM-4-Flash | **免费** | **¥0** |
| DeepSeek | deepseek-chat | ¥0.28 / M tokens | ¥2-5 |
| OpenAI | gpt-4o-mini | ¥0.30 / M tokens | ¥3-6 |
| OpenAI | gpt-4o | ¥3.0 / M tokens | ¥30-60 |

> **新手推荐：** 智谱 GLM-4-Flash 免费，足够写完整本小说。

---

### Q: 能导出吗？会不会把我锁在你们系统里？

**A:** 不会锁。你的稿子在你自己电脑上，随时可以导出：

```bash
openwrite export              # 导出为 Markdown
openwrite export --format txt # 导出为纯文本
```

导出后可以直接在 Word、Typora 或其他编辑器里打开。不需要燃灯也能阅读和编辑。

---

## 使用

### Q: 我写到一半想改大纲怎么办？

**A:** 直接改，燃灯会自动适应。

```bash
# 方案一：手动编辑大纲文件
vim data/novels/你的书/src/outline.md
openwrite sync                # 同步到系统

# 方案二：和策划编辑聊天
openwrite goethe
# "我想把第三篇改成都市情节..."
```

---

### Q: 我觉得 AI 写的风格不对，怎么办？

**A:** 先给 AI 一个参照。

1. 你自己写一段样章（3000 字左右）
2. 让燃灯提取你的风格：

```bash
openwrite style extract my_style --source 你的样章.md
openwrite style synthesize
```

之后再写章节，落笔就会模仿你的风格了。

---

### Q: 角色太多，AI 会乱吗？

**A:** 不会。每个角色都有独立的档案。你可以随时查看：

```bash
# 在 goethe 中问
openwrite goethe
# 在对话里输入: "帮我查看李明的角色档案"
```

角色档案记录了：性格、外貌、说话方式、与其他人的关系、经历过的事件。

---

### Q: 燃灯支持哪些 AI 模型？

**A:** 目前支持：

| 提供商 | 协议 | 免费选项 |
|--------|------|---------|
| OpenAI (GPT-4o / o1) | OpenAI 兼容 | ❌ |
| DeepSeek | OpenAI 兼容 | ❌ |
| 智谱 (GLM-4) | OpenAI 兼容 | ✅ GLM-4-Flash |
| Anthropic (Claude) | Anthropic | ❌ |
| SiliconFlow | OpenAI 兼容 | ❌（送体验额度）|

理论上任何 **兼容 OpenAI API** 的提供商都能用，只需要配置正确的 base_url。

---

## 技术

### Q: 我的书存在哪里？

**A:**

```
项目目录/
├── novel_config.yaml       ← 项目配置
├── data/novels/你的书ID/src/  ← 源文件（你编辑）
│   ├── outline.md
│   ├── characters/
│   └── world/
└── data/novels/你的书ID/data/ ← 运行时数据（自动生成）
    ├── manuscript/          ← 正文手稿
    └── characters/cards/    ← 角色卡片
```

**src/** 里的文件你随便改，其余 AI 自动维护。

---

### Q: 如何切换 AI 模型？

**A:**

```bash
openwrite setup
```

重新运行配置向导，选择新的提供商和模型即可。

也可以直接改环境变量：

```bash
export LLM_PROVIDER=deepseek
export LLM_API_KEY=sk-xxx
export LLM_MODEL=deepseek-chat
export LLM_BASE_URL=https://api.deepseek.com/v1
```

---

### Q: 我的隐私安全吗？我的书稿会被上传吗？

**A:** 燃灯只把你的**大纲、角色设定、当前章节上下文**发送给 AI 模型用于写作。

完整书稿不会上传。正文只存在于你的本地：

- `data/novels/*/data/manuscript/` 目录下
- 导出时写入你指定的路径

燃灯项目本身不收集任何使用数据。

---

### Q: 可以多人协作吗？

**A:** 燃灯目前是单用户工具。但它的所有文件都是纯文本（Markdown / YAML），你可以把整个项目目录放进 Git 仓库，和伙伴一起编辑 src/ 下的源文件，然后同步。

---

### Q: 和 Word / Scrivener / Ulysses 比怎么样？

| 工具 | 强项 |
|------|------|
| Word | 格式排版、打印出版 |
| Scrivener | 非线性写作、卡片管理 |
| Ulysses | 界面优雅、Markdown |
| **燃灯** | **AI 辅助长篇创作、人物一致性、伏笔管理** |

**建议搭配使用：** 燃灯负责"写"，Word / Scrivener 负责"排"。用 `openwrite export` 导出后用其他工具精修格式。
