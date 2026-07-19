#!/usr/bin/env python3
"""燃灯 CLI 入口 — 简化版。

这是 randen 命令的主入口。优先使用简化 CLI（simple_cli.py），
让新手能以中文命令快速上手。

用法:
  randen init           新建一本书（交互式向导）
  randen xie [章号]     写一章（默认写下一章）
  randen kan            查看当前项目状态
  randen shen [章号]    审查章节
  randen gai [章号]     根据审查意见修改
  randen setup          配置模型连接
  randen studio         启动写作工作台 (Web UI)

进阶:
  randen qingdeng       开启青灯规划会话
  randen luobi          开启落笔写作会话
  randen daochu          导出完整书稿 (Markdown/TXT)
  randen daoru <文件>   导入已有书稿
"""

from tools.simple_cli import main

if __name__ == "__main__":
    main()
