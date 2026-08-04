from cimble.check import check_file, check_thresholds

from .conftest import make_file_with_lines


def test_claude_md_boundary_ok_at_120(tmp_project):
    path = tmp_project / "CLAUDE.md"
    make_file_with_lines(path, 120)
    finding = check_file(path)
    assert finding.status == "ok"


def test_claude_md_boundary_over_at_121(tmp_project):
    path = tmp_project / "CLAUDE.md"
    make_file_with_lines(path, 121)
    finding = check_file(path)
    assert finding.status == "over"
    assert "memory/<topic>.md" in finding.hint


def test_claude_md_under_119_is_ok(tmp_project):
    path = tmp_project / "CLAUDE.md"
    make_file_with_lines(path, 119)
    assert check_file(path).status == "ok"


def test_memory_file_boundary_ok_at_120(tmp_project):
    path = tmp_project / "memory" / "index.md"
    make_file_with_lines(path, 120)
    finding = check_file(path)
    assert finding.status == "ok"
    assert finding.kind == "memory"


def test_memory_file_boundary_over_at_121(tmp_project):
    path = tmp_project / "memory" / "backend.md"
    make_file_with_lines(path, 121)
    finding = check_file(path)
    assert finding.status == "over"


def test_non_memory_non_claude_md_file_is_ignored(tmp_project):
    path = tmp_project / "notes.md"
    make_file_with_lines(path, 200)
    assert check_file(path) is None


def test_multiple_nested_memory_files_checked_independently(tmp_project):
    make_file_with_lines(tmp_project / "memory" / "index.md", 200)
    make_file_with_lines(tmp_project / "memory" / "topic-a" / "index.md", 10)
    findings = check_thresholds(tmp_project)
    by_name = {f.path.parent.name: f.status for f in findings if f.kind == "memory"}
    assert by_name["memory"] == "over"
    assert by_name["topic-a"] == "ok"


def test_custom_thresholds_via_arguments(tmp_project):
    path = tmp_project / "CLAUDE.md"
    make_file_with_lines(path, 50)
    finding = check_file(path, file_threshold=40)
    assert finding.status == "over"
