from pathlib import Path

from markdown_it import MarkdownIt


def test_readme_references_external_logo_svg():
    text = Path("README.md").read_text(encoding="utf-8")
    tokens = MarkdownIt().parse(text)

    code_blocks = [token for token in tokens if token.type == "code_block"]
    assert all("<path" not in token.content for token in code_blocks)
    assert "<svg" not in text
    # Branding 已更新为燃灯 — logo 使用纯文字 / shield badge，不再使用 picture/source 标签
    assert "🏮 燃灯" in text
    assert 'src="https://img.shields.io/badge/entry-randen%20luobi' in text
    assert Path("assets/logo-light.svg").exists()
    assert Path("assets/logo-dark.svg").exists()


def test_readme_documents_luobi_as_primary_entry():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "`randen luobi`" in text
    assert "`randen qingdeng`" in text
    assert "`randen write" in text or "randen write" in text
    assert "`randen review" in text or "randen review" in text
    # README 是产品面文档，不再提及 agent 退役细节
    assert "`randen agent` 是主编排入口" not in text
    assert 'randen agent "' not in text


def test_skill_docs_no_longer_present_agent_as_primary_entry():
    root_skill = Path("SKILL.md").read_text(encoding="utf-8")
    goethe_skill = Path("skills/goethe-agent/SKILL.md").read_text(encoding="utf-8")

    assert "落笔是主编排入口" in root_skill
    assert "`write` / `multi-write` / `review`" in root_skill
    assert "`randen agent` 是主编排入口" not in root_skill
    assert "randen luobi" in goethe_skill
    assert 'randen agent "' not in goethe_skill
