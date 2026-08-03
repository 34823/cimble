import pytest


def make_file_with_lines(path, n_lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"line {i}" for i in range(n_lines)) + "\n", encoding="utf-8")


@pytest.fixture
def tmp_project(tmp_path):
    return tmp_path
