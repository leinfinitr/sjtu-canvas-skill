from __future__ import annotations

from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values


def resolve_workspace(workspace: str | None, cwd: str | Path | None = None) -> Path:
    if workspace:
        return Path(workspace).expanduser().resolve()
    return Path(cwd or Path.cwd()).expanduser().resolve()


def load_workspace_env(workspace: str | Path) -> dict[str, str]:
    env_path = Path(workspace) / ".env"
    if not env_path.exists():
        return {}
    values = dotenv_values(env_path)
    return {str(k): str(v) for k, v in values.items() if v is not None}


def get_workspace_cookie(workspace: str | Path, fallback: str | None = None) -> str:
    env = load_workspace_env(workspace)
    cookie = env.get("OC_COOKIE") or fallback or ""
    if not cookie.strip():
        raise RuntimeError(f"OC_COOKIE not found. Put it in {Path(workspace) / '.env'}")
    return cookie.strip()
