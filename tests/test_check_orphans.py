from cimble.check import check_orphans


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_unlinked_and_unmentioned_file_is_orphan(tmp_project):
    memory = tmp_project / "memory"
    _write(memory / "lost.md", "---\nname: project-lost\n---\nnobody points here\n")
    findings = check_orphans(tmp_project)
    (found,) = [f for f in findings if f.slug == "project-lost"]
    assert found.path.name == "lost.md"


def test_file_linked_from_another_memory_file_is_not_orphan(tmp_project):
    memory = tmp_project / "memory"
    _write(memory / "found.md", "---\nname: project-found\n---\nsome content\n")
    _write(memory / "other.md", "---\nname: feedback-other\n---\nsee [[project-found]]\n")
    findings = check_orphans(tmp_project)
    assert not [f for f in findings if f.slug == "project-found"]


def test_file_mentioned_in_claude_md_is_not_orphan(tmp_project):
    memory = tmp_project / "memory"
    _write(memory / "found.md", "---\nname: project-found\n---\nsome content\n")
    _write(tmp_project / "CLAUDE.md", "# Topics\n\n- project-found -> memory/found.md\n")
    findings = check_orphans(tmp_project)
    assert not [f for f in findings if f.slug == "project-found"]


def test_file_linked_via_markdown_link_from_index_is_not_orphan(tmp_project):
    memory = tmp_project / "memory"
    _write(memory / "found.md", "---\nname: project-found\n---\nsome content\n")
    _write(memory / "MEMORY.md", "- [found](found.md) — one-line pointer\n")
    findings = check_orphans(tmp_project)
    assert not [f for f in findings if f.slug == "project-found"]


def test_no_memory_dir_returns_empty(tmp_project):
    assert check_orphans(tmp_project) == []
