from cimble.init import init, init_index, init_topic


def test_creates_claude_md_in_fresh_dir(tmp_project):
    actions = init(tmp_project, project_name="demo")
    assert actions[0].action == "created"
    claude_md = tmp_project / "CLAUDE.md"
    assert claude_md.is_file()
    assert "demo" in claude_md.read_text()


def test_refuses_to_overwrite_existing(tmp_project):
    claude_md = tmp_project / "CLAUDE.md"
    claude_md.write_text("hand-written content\n", encoding="utf-8")
    actions = init(tmp_project)
    assert actions[0].action == "skipped-exists"
    assert claude_md.read_text() == "hand-written content\n"


def test_force_recreates_untouched_cimble_file(tmp_project):
    init(tmp_project, project_name="demo")
    claude_md = tmp_project / "CLAUDE.md"
    before = claude_md.read_text()
    actions = init(tmp_project, project_name="demo", force=True)
    assert actions[0].action == "created"
    assert claude_md.read_text() == before


def test_force_does_not_override_human_edited_file(tmp_project):
    claude_md = tmp_project / "CLAUDE.md"
    claude_md.write_text("hand-written, no cimble marker\n", encoding="utf-8")
    actions = init(tmp_project, force=True)
    assert actions[0].action == "skipped-exists"
    assert claude_md.read_text() == "hand-written, no cimble marker\n"


def test_dry_run_writes_nothing(tmp_project):
    actions = init(tmp_project, project_name="demo", dry_run=True)
    assert all(a.action == "skipped-dry-run" for a in actions)
    assert not (tmp_project / "CLAUDE.md").exists()


def test_init_index_creates_memory_index_backlinked_to_claude_md(tmp_project):
    action = init_index(tmp_project, project_name="demo")
    assert action.action == "created"
    index_path = tmp_project / "memory" / "index.md"
    assert index_path.is_file()
    assert index_path.read_text().splitlines()[0] == "↑ ../CLAUDE.md"


def test_init_topic_backlinks_to_claude_md_when_no_index(tmp_project):
    action = init_topic(tmp_project, "backend", project_name="demo")
    topic_path = tmp_project / "memory" / "backend.md"
    assert action.action == "created"
    assert topic_path.read_text().splitlines()[0] == "↑ ../CLAUDE.md"


def test_init_topic_backlinks_to_index_when_index_exists(tmp_project):
    init_index(tmp_project, project_name="demo")
    action = init_topic(tmp_project, "backend", project_name="demo")
    topic_path = tmp_project / "memory" / "backend.md"
    assert action.action == "created"
    assert topic_path.read_text().splitlines()[0] == "↑ index.md"
