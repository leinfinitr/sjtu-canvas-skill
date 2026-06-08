# SJTU Canvas review workflow notes

Use this when the user asks to review SJTU Canvas course lectures using course videos/subtitles plus a named course material file.

## Workflow

1. Resolve course name to `course_id` with `uv run main --json list-courses`; never guess IDs.
2. Discover target videos with `uv run main --json list-videos <course_id>` and match `video_name` by lecture number, e.g. `第29讲`.
3. Discover the material with `uv run main --json list-files <course_id>` and match by filename, e.g. `hand16.pdf`.
4. Download the material using its fresh `url` field:

```bash
uv run main --json download-file "<file_url>" --path "./course-workspaces/<course-name>/materials"
```

5. Download subtitles for each located video:

```bash
uv run main --json download-subtitle <course_id> --video-id '<video_id>' --out "./course-workspaces/<course-name>/reviews"
```

6. Extract PDF text locally when needed:

```bash
uv run python - <<'PY'
from pathlib import Path
import fitz, json
pdf = Path('course-workspaces/<course-name>/materials/<file>.pdf')
out = pdf.with_suffix('.txt')
doc = fitz.open(pdf)
out.write_text('\n'.join(f'\n\n===== PAGE {i} =====\n' + p.get_text() for i, p in enumerate(doc, 1)), encoding='utf-8')
print(json.dumps({'pdf': str(pdf), 'pages': len(doc), 'txt': str(out), 'chars': out.stat().st_size}, ensure_ascii=False))
PY
```

7. Combine PDF structure with transcript details into a durable review note under `course-workspaces/<course-name>/reviews/`.

## Review-note shape

For lecture review, produce:

- Source paths and any missing-source caveat.
- One-sentence theme.
- Concept map / relationships.
- Lecture-by-lecture summary.
- Definitions and theorem statements.
- Proof templates or reduction templates.
- Common pitfalls.
- Self-test questions with answers.
- Suggested review order.

## Pitfalls

- `list-videos` can fail with `未找到新版课堂视频入口...` when `OC_COOKIE` is stale even if `TOKEN` and `list-files` still work. Verify video auth separately by checking whether a request to `https://oc.sjtu.edu.cn/courses/<course_id>` redirects to `/login/canvas` or contains the `课堂视频` link.
- The skill loads `.env` via python-dotenv; shell `source .env` may fail when cookie values contain quotes, semicolons, or spaces. Do not rely on shell-sourcing cookie files. Let the CLI/python-dotenv load `.env`, or pass `OC_COOKIE` through the process environment safely.
- If the requested lecture is not present in `list-videos`, state the caveat and use available sources instead of inventing a transcript.
- Avoid destructive cleanup such as `rm -rf` in verification steps; create a new output directory instead.
- If a previously missing lecture appears after the user refreshes `OC_COOKIE`, follow `references/incremental-review-updates.md`: re-list videos, download the late subtitle, verify readability, then patch the existing note and remove stale caveats instead of creating a duplicate note.
