import json
import os
import subprocess
import sys
import time
from pathlib import Path

from cimble.audit import audit_project, find_projects
from cimble.check import check_file, check_thresholds, find_claude_md_files
from cimble.codex_hook import candidate_paths, project_scopes, warnings


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_agents_preferred_over_claude_wrapper(tmp_path):
    agents = write(tmp_path / 'AGENTS.md', '# rules\n' + 'line\n' * 121)
    wrapper = write(tmp_path / 'CLAUDE.md', '@AGENTS.md\n')
    legacy = write(tmp_path / 'nested/CLAUDE.md', '# legacy\n')
    assert find_claude_md_files(tmp_path) == [agents, legacy]
    assert check_file(wrapper).path == agents
    assert check_file(wrapper).status == 'over'
    assert len(check_thresholds(tmp_path)) == 2


def test_agents_uses_same_instruction_threshold(tmp_path):
    path = write(tmp_path / 'AGENTS.md', 'line\n' * 121)
    assert check_file(path).status == 'over'
    assert check_file(path, claude_md_threshold=200).status == 'ok'


def test_agents_only_audit_and_parent_discovery(tmp_path):
    project = tmp_path / 'project'
    write(project / 'AGENTS.md', '# rules\n')
    write(project / 'memory/topic.md', '↑ ../AGENTS.md\n')
    assert find_projects(project) == [project]
    assert find_projects(tmp_path, each=True) == [project]
    result = audit_project(project)
    assert not result.backlinks
    assert not result.over_files


def test_agents_index_prevents_false_orphan(tmp_path):
    write(tmp_path / 'AGENTS.md', '# rules\n[topic](memory/my-topic.md)\n')
    write(tmp_path / 'CLAUDE.md', '@AGENTS.md\n')
    write(tmp_path / 'memory/my-topic.md', '↑ ../AGENTS.md\n')
    assert not audit_project(tmp_path).orphans


def test_codex_patch_paths_resolve_relative_and_move(tmp_path):
    payload = {'cwd': str(tmp_path), 'tool_input': {'command': '*** Begin Patch\n*** Update File: AGENTS.md\n*** Move to: nested/AGENTS.md\n*** End Patch'}}
    _, explicit = candidate_paths(payload, tmp_path / 'home')
    assert explicit == {tmp_path / 'AGENTS.md', tmp_path / 'nested/AGENTS.md'}


def test_codex_cache_warns_on_edit_once_and_reads_actual_wrapper(tmp_path):
    path = write(tmp_path / 'AGENTS.md', '## topic\n' + 'line\n' * 121)
    write(tmp_path / 'CLAUDE.md', '@AGENTS.md\n')
    state = tmp_path / 'state.json'
    payload = {'cwd': str(tmp_path), 'tool_input': {'file_path': str(tmp_path / 'CLAUDE.md')}}
    result = warnings(payload, state, home=tmp_path / 'home')
    assert sum('122 lines' in m for m in result) == 1
    assert any('## topic' in m for m in result)
    assert warnings(payload, state, home=tmp_path / 'home') == []
    path.write_text('## topic\nshort\n')
    assert warnings(payload, state, home=tmp_path / 'home') == []


def test_first_shell_event_ignores_old_files_but_later_edit_warns(tmp_path):
    path = write(tmp_path / 'AGENTS.md', 'line\n' * 121)
    old = time.time() - 60
    os.utime(path, (old, old))
    state = tmp_path / 'state.json'
    payload = {'cwd': str(tmp_path), 'tool_name': 'Bash', 'tool_input': {'command': 'opaque Python script'}}
    assert warnings(payload, state, home=tmp_path / 'home') == []
    path.write_text('line\n' * 122)
    assert any('122 lines' in m for m in warnings(payload, state, home=tmp_path / 'home'))


def test_shell_event_observes_immediate_project_and_auto_memory(tmp_path):
    write(tmp_path / 'project/AGENTS.md', 'line\n' * 121)
    home = tmp_path / 'home'
    auto = home / '.claude/projects' / str(tmp_path).replace('/', '-') / 'memory/feedback.md'
    write(auto, 'line\n' * 121)
    payload = {'cwd': str(tmp_path), 'tool_name': 'Bash', 'tool_input': {'command': 'opaque'}}
    result = warnings(payload, tmp_path / 'state.json', home=home)
    assert any('project/AGENTS.md' in m for m in result)
    assert any('feedback.md' in m for m in result)


def test_memory_scan_does_not_follow_symlinks_or_archives(tmp_path):
    write(tmp_path / 'AGENTS.md', '# root\n')
    write(tmp_path / 'graveyard/AGENTS.md', 'line\n' * 150)
    write(tmp_path / 'elsewhere/hidden.md', 'line\n' * 150)
    (tmp_path / 'memory').symlink_to(tmp_path / 'elsewhere', target_is_directory=True)
    paths, _ = candidate_paths({'cwd': str(tmp_path)}, tmp_path / 'home')
    assert tmp_path / 'graveyard/AGENTS.md' not in paths
    assert tmp_path / 'memory/hidden.md' not in paths


def test_worktree_includes_main_checkout(tmp_path):
    main = tmp_path / 'main'
    main.mkdir()
    subprocess.run(['git', 'init', str(main)], check=True, capture_output=True)
    subprocess.run(['git', '-C', str(main), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                    'commit', '--allow-empty', '-m', 'init'], check=True, capture_output=True)
    worktree = tmp_path / 'worktree'
    subprocess.run(['git', '-C', str(main), 'worktree', 'add', '-b', 'test', str(worktree)],
                   check=True, capture_output=True)
    assert main in project_scopes(worktree)


def test_codex_module_outputs_nonblocking_context(tmp_path):
    path = write(tmp_path / 'AGENTS.md', 'line\n' * 121)
    env = dict(os.environ, CIMBLE_CODEX_CACHE=str(tmp_path / 'cache'))
    result = subprocess.run([sys.executable, '-m', 'cimble.codex_hook'],
                            input=json.dumps({'cwd': str(tmp_path), 'tool_input': {'file_path': str(path)}}),
                            text=True, capture_output=True, env=env)
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out['hookSpecificOutput']['hookEventName'] == 'PostToolUse'
    assert '121 lines' in out['hookSpecificOutput']['additionalContext']


def test_claude_hook_checks_agents(tmp_path):
    path = write(tmp_path / 'AGENTS.md', 'line\n' * 121)
    hook = Path(__file__).parents[1] / 'hooks/check_memory_hook.py'
    result = subprocess.run([sys.executable, str(hook)], input=json.dumps({'tool_input': {'file_path': str(path)}}),
                            capture_output=True, text=True)
    assert result.returncode == 0
    assert '121 lines' in json.loads(result.stdout)['systemMessage']


def test_dispatcher_threshold_does_not_leak_into_child_project(tmp_path):
    write(tmp_path / 'cimble.toml', '[cimble]\nclaude_md_threshold = 400\n')
    path = write(tmp_path / 'project/AGENTS.md', 'line\n' * 121)
    result = warnings({'cwd': str(tmp_path), 'tool_input': {'file_path': str(path)}},
                      tmp_path / 'state.json', home=tmp_path / 'home')
    assert any('threshold 120' in message and str(path) in message for message in result)
