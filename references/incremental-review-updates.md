# SJTU Canvas incremental lecture-review updates

Use this when a review note was already generated from Canvas materials and some sources arrive later (for example, a renewed `OC_COOKIE` makes a missing lecture video/subtitle appear).

## Pattern

1. Re-verify video auth without exposing cookie contents:

```bash
cd "$LOCALAPPDATA/hermes/skills/sjtu-canvas-skill"
uv run python - <<'PY'
from dotenv import dotenv_values
from scripts.video_client import SJTUVideoClient
cookie = dotenv_values('.env').get('OC_COOKIE') or ''
print('cookie_len', len(cookie))
vc = SJTUVideoClient(cookie)
r = vc.session.get('https://oc.sjtu.edu.cn/courses/<course_id>', timeout=30)
print('course_page_status', r.status_code)
print('final_url', r.url)
print('has_classroom_video_text', '课堂视频' in r.text)
print('redirected_to_login', '/login/' in r.url)
try:
    print('external_tool_id', vc.get_external_tool_id(<course_id>))
except Exception as e:
    print('external_tool_error', type(e).__name__, str(e))
PY
```

2. Re-list videos and match the newly requested lecture by `video_name`, not by position:

```bash
uv run main --json list-videos <course_id> > "$TEMP/videos_<course_id>.json"
python - <<'PY'
import json, os
p = os.environ['TEMP'] + '/videos_<course_id>.json'
data = json.load(open(p, encoding='utf-8'))
needle = '第30讲'
print(json.dumps({
    'count': len(data) if isinstance(data, list) else None,
    'matches': [v for v in data if needle in v.get('video_name','')] if isinstance(data, list) else data,
    'tail': data[-5:] if isinstance(data, list) else None,
}, ensure_ascii=False))
PY
```

3. Download the subtitle into the stable course workspace:

```bash
uv run main --json download-subtitle <course_id> --video-id '<video_id>' --out './course-workspaces/<course-name>/reviews'
```

4. Verify transcript readability and line count with `read_file` or a small Python snippet before editing the note. Do not just trust the success JSON.

5. Patch the existing review note, rather than creating a second competing note:
   - Remove stale missing-source caveats.
   - Update the source line to include the newly available transcript.
   - Add concise transcript-derived classroom emphasis under the relevant section.
   - Preserve earlier PDF-based structure if it remains useful.
   - Add or update self-test questions if the transcript emphasized exam-relevant points.

## Good additions when a late transcript arrives

- Instructor emphasis, e.g. “考试百分之百” for a proof template.
- Quizzes discussed in class and their answer rationale.
- Corrections to earlier caveats (“第30讲字幕 previously unavailable” → source now available).
- Connections the instructor verbally emphasized but the slides only imply.

## Pitfalls

- A renewed cookie may make a previously missing lecture appear. Re-run `list-videos`; do not assume the old video count is still authoritative.
- Do not shell-`source` `.env` for `OC_COOKIE`; cookie values can contain quotes, semicolons, and spaces. Let python-dotenv/CLI load it.
- Avoid broad rewrites that shrink a useful note accidentally. When patching with scripts, verify key phrases and total line count afterward.
