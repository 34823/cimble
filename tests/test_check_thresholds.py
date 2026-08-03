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
    assert "constitution.md" in finding.hint


def test_claude_md_under_119_is_ok(tmp_project):
    path = tmp_project / "CLAUDE.md"
    make_file_with_lines(path, 119)
    assert check_file(path).status == "ok"


def test_constitution_boundary_ok_at_150(tmp_project):
    path = tmp_project / "memory" / "constitution.md"
    make_file_with_lines(path, 150)
    finding = check_file(path)
    assert finding.status == "ok"


def test_constitution_boundary_over_at_151(tmp_project):
    path = tmp_project / "memory" / "constitution.md"
    make_file_with_lines(path, 151)
    finding = check_file(path)
    assert finding.status == "over"
    assert "topic" in finding.hint


def test_constitution_under_149_is_ok(tmp_project):
    path = tmp_project / "memory" / "constitution.md"
    make_file_with_lines(path, 149)
    assert check_file(path).status == "ok"


def test_constitution_md_outside_memory_dir_is_ignored(tmp_project):
    path = tmp_project / "constitution.md"
    make_file_with_lines(path, 200)
    assert check_file(path) is None


def test_multiple_nested_constitutions_checked_independently(tmp_project):
    make_file_with_lines(tmp_project / "memory" / "constitution.md", 200)
    make_file_with_lines(tmp_project / "memory" / "topic-a" / "constitution.md", 10)
    findings = check_thresholds(tmp_project)
    by_status = {f.path.parent.name: f.status for f in findings if f.kind == "constitution"}
    assert by_status["memory"] == "over"
    assert by_status["topic-a"] == "ok"


def test_custom_thresholds_via_arguments(tmp_project):
    path = tmp_project / "CLAUDE.md"
    make_file_with_lines(path, 50)
    finding = check_file(path, claude_md_threshold=40)
    assert finding.status == "over"
