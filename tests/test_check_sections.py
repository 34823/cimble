from cimble.check import check_all_sections, check_sections


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_section_under_threshold_is_ok(tmp_project):
    path = tmp_project / "CLAUDE.md"
    body = "\n".join(f"line {i}" for i in range(10))
    _write(path, f"# Title\n\n## Small\n\n{body}\n")
    (finding,) = check_sections(path, section_threshold=40)
    assert finding.heading == "Small"
    assert finding.status == "ok"


def test_section_over_threshold_is_flagged(tmp_project):
    path = tmp_project / "CLAUDE.md"
    body = "\n".join(f"line {i}" for i in range(41))
    _write(path, f"# Title\n\n## Big\n\n{body}\n")
    (finding,) = check_sections(path, section_threshold=40)
    assert finding.status == "over"
    assert "memory/<topic>.md" in finding.hint


def test_multiple_sections_checked_independently(tmp_project):
    small = "\n".join(f"line {i}" for i in range(5))
    big = "\n".join(f"line {i}" for i in range(41))
    _write(tmp_project / "CLAUDE.md", f"# Title\n\n## Small\n\n{small}\n\n## Big\n\n{big}\n")
    findings = check_sections(tmp_project / "CLAUDE.md", section_threshold=40)
    by_heading = {f.heading: f.status for f in findings}
    assert by_heading["Small"] == "ok"
    assert by_heading["Big"] == "over"


def test_content_before_first_heading_is_not_a_section(tmp_project):
    body = "\n".join(f"line {i}" for i in range(200))
    _write(tmp_project / "CLAUDE.md", f"# Title\n\n{body}\n")
    assert check_sections(tmp_project / "CLAUDE.md", section_threshold=40) == []


def test_check_all_sections_scans_claude_md_and_memory(tmp_project):
    big = "\n".join(f"line {i}" for i in range(41))
    _write(tmp_project / "CLAUDE.md", f"# T\n\n## A\n\n{big}\n")
    _write(tmp_project / "memory" / "index.md", f"# T\n\n## B\n\n{big}\n")
    findings = check_all_sections(tmp_project, section_threshold=40)
    headings = {f.heading for f in findings}
    assert headings == {"A", "B"}
