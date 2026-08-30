from cimble.check import check_backlinks


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_missing_backlink_is_flagged(tmp_project):
    _write(tmp_project / "memory" / "index.md", "# No backlink here\n")
    (finding,) = check_backlinks(tmp_project)
    assert finding.status == "missing"


def test_broken_backlink_is_flagged(tmp_project):
    _write(tmp_project / "memory" / "index.md", "↑ ../CLAUDE.md\n\n# Index\n")
    (finding,) = check_backlinks(tmp_project)
    assert finding.status == "broken"


def test_backlink_to_existing_claude_md_is_ok(tmp_project):
    _write(tmp_project / "CLAUDE.md", "# CLAUDE.md\n")
    _write(tmp_project / "memory" / "index.md", "↑ ../CLAUDE.md\n\n# Index\n")
    (finding,) = check_backlinks(tmp_project)
    assert finding.status == "ok"


def test_chain_through_index_to_claude_md_is_ok(tmp_project):
    _write(tmp_project / "CLAUDE.md", "# CLAUDE.md\n")
    _write(tmp_project / "memory" / "index.md", "↑ ../CLAUDE.md\n\n# Index\n")
    _write(tmp_project / "memory" / "backend.md", "↑ index.md\n\n# Backend\n")
    findings = {f.path.name: f.status for f in check_backlinks(tmp_project)}
    assert findings["index.md"] == "ok"
    assert findings["backend.md"] == "ok"


def test_cyclic_backlink_chain_is_flagged(tmp_project):
    _write(tmp_project / "memory" / "a.md", "↑ b.md\n\n# A\n")
    _write(tmp_project / "memory" / "b.md", "↑ a.md\n\n# B\n")
    findings = {f.path.name: f.status for f in check_backlinks(tmp_project)}
    assert findings["a.md"] == "cyclic"
    assert findings["b.md"] == "cyclic"


def test_markdown_link_backlink_is_ok(tmp_project):
    _write(tmp_project / "CLAUDE.md", "# CLAUDE.md\n")
    _write(tmp_project / "memory" / "index.md", "↑ [../CLAUDE.md](../CLAUDE.md)\n\n# Index\n")
    (finding,) = check_backlinks(tmp_project)
    assert finding.status == "ok"


def test_backlink_after_frontmatter_is_ok(tmp_project):
    _write(tmp_project / "CLAUDE.md", "# CLAUDE.md\n")
    _write(
        tmp_project / "memory" / "index.md",
        "---\nname: index\ndescription: test\n---\n\n↑ [../CLAUDE.md](../CLAUDE.md)\n\n# Index\n",
    )
    (finding,) = check_backlinks(tmp_project)
    assert finding.status == "ok"
