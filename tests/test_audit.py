import os
import time

from cimble.audit import audit_project, find_projects, render_markdown


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_find_projects_expands_parent_folder(tmp_path):
    _write(tmp_path / "a" / "CLAUDE.md", "# a\n")
    _write(tmp_path / "b" / "notes.md", "x\n")
    assert find_projects(tmp_path) == [tmp_path / "a"]


def test_audit_reports_stale_and_duplicate_lines(tmp_path):
    line = "this exact sentence is long enough to count as a duplicated line across files"
    _write(tmp_path / "CLAUDE.md", "# p\n")
    _write(tmp_path / "memory" / "x.md", f"↑ ../CLAUDE.md\n{line}\n")
    _write(tmp_path / "memory" / "y.md", f"↑ ../CLAUDE.md\n{line}\n")
    old = time.time() - 90 * 86400
    os.utime(tmp_path / "memory" / "x.md", (old, old))
    result = audit_project(tmp_path, stale_days=60)
    assert [(p.name, age) for p, age in result.stale] == [("x.md", 90)]
    assert len(result.duplicates) == 1
    text = render_markdown([result], tmp_path.parent)
    assert "stale (90 d" in text and "duplicate line" in text


def test_clean_project_has_no_issues(tmp_path):
    _write(tmp_path / "CLAUDE.md", "# p\n")
    assert audit_project(tmp_path).issue_count == 0
