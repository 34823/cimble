from cimble.check import check_wikilinks


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_wikilink_resolves_via_frontmatter_name(tmp_project):
    memory = tmp_project / "memory"
    _write(memory / "a.md", "---\nname: topic-a\n---\nsee [[topic-a]]\n")
    _write(memory / "b.md", "---\nname: topic-b\n---\nno links here\n")
    findings = check_wikilinks(memory)
    (found,) = [f for f in findings if f.target == "topic-a"]
    assert found.resolved


def test_wikilink_resolves_via_filename_stem_fallback(tmp_project):
    memory = tmp_project / "memory"
    _write(memory / "conventions.md", "no frontmatter here\n")
    _write(memory / "a.md", "see [[conventions]]\n")
    findings = check_wikilinks(memory)
    (found,) = [f for f in findings if f.target == "conventions"]
    assert found.resolved


def test_wikilink_missing_target_is_flagged(tmp_project):
    memory = tmp_project / "memory"
    _write(memory / "a.md", "see [[does-not-exist]]\n")
    findings = check_wikilinks(memory)
    (found,) = [f for f in findings if f.target == "does-not-exist"]
    assert not found.resolved
