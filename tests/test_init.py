from cimble.init import init


def test_stage1_creates_claude_md_in_fresh_dir(tmp_project):
    actions = init(tmp_project, stage=1, project_name="demo")
    assert actions[0].action == "created"
    claude_md = tmp_project / "CLAUDE.md"
    assert claude_md.is_file()
    assert "demo" in claude_md.read_text()


def test_stage1_refuses_to_overwrite_existing(tmp_project):
    claude_md = tmp_project / "CLAUDE.md"
    claude_md.write_text("hand-written content\n", encoding="utf-8")
    actions = init(tmp_project, stage=1)
    assert actions[0].action == "skipped-exists"
    assert claude_md.read_text() == "hand-written content\n"


def test_force_recreates_untouched_cimble_file(tmp_project):
    init(tmp_project, stage=1, project_name="demo")
    claude_md = tmp_project / "CLAUDE.md"
    before = claude_md.read_text()
    actions = init(tmp_project, stage=1, project_name="demo", force=True)
    assert actions[0].action == "created"
    assert claude_md.read_text() == before


def test_force_does_not_override_human_edited_file(tmp_project):
    claude_md = tmp_project / "CLAUDE.md"
    claude_md.write_text("hand-written, no cimble marker\n", encoding="utf-8")
    actions = init(tmp_project, stage=1, force=True)
    assert actions[0].action == "skipped-exists"
    assert claude_md.read_text() == "hand-written, no cimble marker\n"


def test_stage2_creates_both_files_in_fresh_dir(tmp_project):
    actions = init(tmp_project, stage=2, project_name="demo")
    paths = {a.path.name: a.action for a in actions}
    assert paths["CLAUDE.md"] == "created"
    assert paths["constitution.md"] == "created"
    assert (tmp_project / "memory" / "constitution.md").is_file()


def test_stage2_leaves_existing_claude_md_untouched(tmp_project):
    claude_md = tmp_project / "CLAUDE.md"
    claude_md.write_text("existing operational content\n", encoding="utf-8")
    actions = init(tmp_project, stage=2, project_name="demo")
    claude_action = next(a for a in actions if a.path.name == "CLAUDE.md")
    assert claude_action.action == "skipped-exists"
    assert claude_md.read_text() == "existing operational content\n"
    assert (tmp_project / "memory" / "constitution.md").is_file()


def test_dry_run_writes_nothing(tmp_project):
    actions = init(tmp_project, stage=2, project_name="demo", dry_run=True)
    assert all(a.action == "skipped-dry-run" for a in actions)
    assert not (tmp_project / "CLAUDE.md").exists()
    assert not (tmp_project / "memory").exists()
