from pathlib import Path

from scripts.workspace import load_workspace_env, resolve_workspace


def test_resolve_workspace_defaults_to_current_dir(tmp_path):
    assert resolve_workspace(None, cwd=tmp_path) == tmp_path


def test_load_workspace_env_reads_oc_cookie(tmp_path):
    (tmp_path / ".env").write_text("OC_COOKIE=a=1; b=2\n", encoding="utf-8")
    env = load_workspace_env(tmp_path)
    assert env["OC_COOKIE"] == "a=1; b=2"
