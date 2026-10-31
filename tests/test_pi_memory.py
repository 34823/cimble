"""Pi can opt out of legacy storage and exclude generated memory explicitly."""
from cimble.codex_hook import candidate_paths, warnings


def test_pi_does_not_probe_claude_memory(tmp_path, monkeypatch):
    home = tmp_path / 'home'
    project = tmp_path / 'project'
    project.mkdir()
    legacy = home / '.claude/projects' / str(project).replace('/', '-') / 'memory'
    legacy.mkdir(parents=True)
    note = legacy / 'feedback.md'
    note.write_text('line\n' * 150)
    monkeypatch.setenv('CIMBLE_LEGACY_CLAUDE_MEMORY', '0')
    paths, _ = candidate_paths({'cwd': str(project)}, home)
    assert note not in paths


def test_generated_excluded_even_explicit_and_alias(tmp_path, monkeypatch):
    generated = tmp_path / 'memory/codex'
    generated.mkdir(parents=True)
    note = generated / 'summary.md'
    note.write_text('line\n' * 150)
    alias = tmp_path / 'alias.md'
    alias.symlink_to(note)
    monkeypatch.setenv('CIMBLE_IGNORE_PATHS', str(generated))
    monkeypatch.setenv('CIMBLE_LEGACY_CLAUDE_MEMORY', '0')
    for path in (note, alias):
        payload = {'cwd': str(tmp_path), 'tool_input': {'file_path': str(path)}}
        paths, explicit = candidate_paths(payload, tmp_path)
        assert note not in paths
        assert not explicit
        assert not warnings(payload, tmp_path / 'cache.json', home=tmp_path)
