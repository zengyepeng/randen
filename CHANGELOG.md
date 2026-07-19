# Changelog

All notable changes to 燃灯 (Randen) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-07-19

### 🏮 燃灯初燃

燃灯 (Randen) 正式诞生，继承自 [OpenWrite](https://github.com/LiPu-jpg/Openwrite) v5.8.0。

### ✨ 品牌升级

- **OpenWrite → 燃灯 (Randen)**：从"开源写作工具"升级为"长篇小说 AI 写作合伙人"
- **Goethe → 青灯 (Qingdeng)**：长期规划 Agent，负责灵感整理、人物设定、大纲规划
- **Dante → 落笔 (Luobi)**：正文创作主 Agent，负责写作、37 维度审查、状态结算
- **Studio → 灯台 (Dengtai)**：写作工作台
- 标语：「燃灯一盏，故事自成」

### 📝 文档重构

- 全新 README.md：中文优先，痛点叙事，情绪感染力
- SKILL.md 重构：修复子技能引用断裂，统一青灯/落笔入口
- 新增 `@quick-reference` 缓存优化段
- 新增 pyproject.toml、.gitignore、LICENSE、CHANGELOG.md
- 新增 bin/randen、bin/qingdeng、bin/luobi CLI 入口

### 🔧 技术继承

- 源码继承自 OpenWrite v5.8.0（`tools/`、`models/`、`skills/`、`tests/`）
- 所有功能逻辑保持不变，仅品牌命名更新
- Canonical packet 组装、两阶段写作、37 维度审查、真相文件管理等核心机制完整保留
