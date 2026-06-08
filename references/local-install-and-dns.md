# SJTU Canvas skill local troubleshooting notes

This note captures durable operational details discovered while installing and validating `sjtu-canvas-skill` on the user's Windows Git Bash Hermes environment.

## Raw SKILL.md install omits CLI implementation

`hermes skills install https://raw.githubusercontent.com/leinfinitr/sjtu-canvas-skill/main/SKILL.md --yes --force` installs only `SKILL.md`. The CLI commands in the skill require the repository implementation files. After installing from raw `SKILL.md`, clone the repository and copy these into the installed skill directory:

```bash
git clone https://github.com/leinfinitr/sjtu-canvas-skill.git /tmp/sjtu-canvas-skill
SKILL_DIR="$LOCALAPPDATA/hermes/skills/sjtu-canvas-skill"
cp -R /tmp/sjtu-canvas-skill/scripts "$SKILL_DIR/"
cp /tmp/sjtu-canvas-skill/pyproject.toml /tmp/sjtu-canvas-skill/uv.lock /tmp/sjtu-canvas-skill/README.md "$SKILL_DIR/"
cd "$SKILL_DIR"
uv run main --help
```

## Non-interactive credential check

Before running Canvas API commands, verify credentials are visible without printing secret values:

```bash
cd "$LOCALAPPDATA/hermes/skills/sjtu-canvas-skill"
printf 'TOKEN=%s\n' "$( [ -n "$TOKEN" ] && echo SET || echo MISSING )"
printf 'BASE_URL=%s\n' "$( [ -n "$BASE_URL" ] && echo SET || echo MISSING )"
printf 'OC_COOKIE=%s\n' "$( [ -n "$OC_COOKIE" ] && echo SET || echo MISSING )"
```

If `TOKEN` is missing, `uv run main --json list-courses` can prompt for it and hang in non-interactive tool calls. The skill's `scripts/main.py` loads `.env` from the skill directory, so `TOKEN` and `OC_COOKIE` may be present there even if not exported in the parent shell.

## Windows aiohttp / aiodns timeout workaround

On this setup, `uv run main --json get-me` initially failed with:

```text
Cannot connect to host oc.sjtu.edu.cn:443 ssl:default [Timeout while contacting DNS servers]
```

`curl -I https://oc.sjtu.edu.cn` and Python `socket.getaddrinfo('oc.sjtu.edu.cn', 443)` both worked, so the problem was aiohttp using aiodns rather than the system resolver. The local fix in `scripts/client.py` was to use a custom resolver backed by `socket.getaddrinfo` on Windows and force IPv4 for the aiohttp `TCPConnector`.

Minimal pattern:

```python
import asyncio, socket, sys, aiohttp
from aiohttp.abc import AbstractResolver

class _SystemResolver(AbstractResolver):
    async def resolve(self, host, port=0, family=socket.AF_INET):
        infos = await asyncio.to_thread(socket.getaddrinfo, host, port, family, socket.SOCK_STREAM)
        return [
            {"hostname": host, "host": address[0], "port": address[1], "family": fam, "proto": proto, "flags": 0}
            for fam, _typ, proto, _cname, address in infos
        ]
    async def close(self):
        return None

def _connector_kwargs():
    if sys.platform.startswith("win"):
        return {"resolver": _SystemResolver(), "family": socket.AF_INET}
    return {}

# In aiohttp.ClientSession(...):
connector=aiohttp.TCPConnector(**_connector_kwargs())
```

Verification commands after the fix:

```bash
uv run main --json get-me
uv run main --json list-courses
uv run main --json list-files <course_id>
```

## Classroom video caveat

`OC_COOKIE` can be present and readable while `list-videos` still returns:

```text
未找到新版课堂视频入口，可能是课程未开放课堂视频或页面结构已变化。
```

Interpret this narrowly: Canvas API token and course-file workflows may be healthy; this message only means the current course page did not expose the specific “课堂视频” external-tool link pattern expected by `scripts/video_client.py`, or the page structure changed. Do not treat it as evidence that TOKEN is invalid.
