from cimble.check import check_missing_links


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_plain_mention_without_link_is_flagged(tmp_project):
    memory = tmp_project / "memory"
    _write(memory / "gnsh.md", "---\nname: project-gnsh\n---\nthe gnsh platform runs on port 8600\n")
    _write(memory / "deploy.md", "---\nname: feedback-deploy\n---\ndeploy notes mention project-gnsh here\n")
    findings = check_missing_links(tmp_project)
    (found,) = [f for f in findings if f.target_slug == "project-gnsh"]
    assert found.path.name == "deploy.md"


def test_already_linked_mention_is_not_flagged(tmp_project):
    memory = tmp_project / "memory"
    _write(memory / "gnsh.md", "---\nname: project-gnsh\n---\nsome content\n")
    _write(memory / "deploy.md", "---\nname: feedback-deploy\n---\nsee [[project-gnsh]] for details\n")
    findings = check_missing_links(tmp_project)
    assert not [f for f in findings if f.target_slug == "project-gnsh"]


def test_unrelated_file_is_not_flagged(tmp_project):
    memory = tmp_project / "memory"
    _write(memory / "gnsh.md", "---\nname: project-gnsh\n---\nsome content\n")
    _write(memory / "unrelated.md", "---\nname: feedback-unrelated\n---\nnothing to see here\n")
    findings = check_missing_links(tmp_project)
    assert not [f for f in findings if f.target_slug == "project-gnsh"]


def test_markdown_link_counts_as_linked(tmp_project):
    memory = tmp_project / "memory"
    _write(memory / "gnsh.md", "---\nname: project-gnsh\n---\nsome content\n")
    _write(memory / "index.md", "- [gnsh](gnsh.md) — project-gnsh pointer\n")
    findings = check_missing_links(tmp_project)
    assert not [f for f in findings if f.target_slug == "project-gnsh"]


def test_single_word_slug_is_never_a_target(tmp_project):
    memory = tmp_project / "memory"
    _write(memory / "index.md", "no frontmatter\n")  # slug falls back to stem "index"
    _write(memory / "other.md", "---\nname: feedback-other\n---\nsee the index for more\n")
    findings = check_missing_links(tmp_project)
    assert not [f for f in findings if f.target_slug == "index"]


def test_no_memory_dir_returns_empty(tmp_project):
    assert check_missing_links(tmp_project) == []
