# Windows local review workflow pitfalls

Use this reference for SJTU Canvas review-note work on the user's Windows Git Bash Hermes setup, especially when the workspace is under `D:/Course/...` and the skill lives under `%LOCALAPPDATA%/hermes/skills/sjtu-canvas-skill`.

## Verify actual tool backend after reloads

If file/terminal tools unexpectedly report an SSH backend or another remote environment, do not assume the user's stated config is wrong. First ask them to run `/reload` or `/reset` if needed, then immediately verify with a harmless live probe:

```bash
printf 'SHELL=%s\n' "$SHELL"
uname -a 2>/dev/null || ver
whoami
pwd
python - <<'PY'
import os, platform, sys
print('python', sys.executable)
print('platform', platform.platform())
print('LOCALAPPDATA', os.environ.get('LOCALAPPDATA'))
print('HERMES_HOME', os.environ.get('HERMES_HOME'))
PY
```

A successful local Windows/Git-Bash probe will typically show `MINGW64_NT...`, `/d/...` paths, and `LOCALAPPDATA=C:\Users\...\AppData\Local`. Once this is verified, proceed with the local course workspace rather than giving more backend-switching advice.

## Avoid Python `Path('/tmp')` for Git Bash temp files

In Windows Git Bash, shell redirection to `/tmp/foo.json` and Python's `Path('/tmp/foo.json')` may not refer to the same path when Python is native Windows. Prefer writing temporary JSON files in the current working directory, e.g. `sjtu_courses_tmp.json`, then read them from Python with `Path('sjtu_courses_tmp.json')`.

## Downloaded subtitles may be nested

`uv run main --json download-subtitle <course_id> --video-id <id> --out <out>` can create a nested directory like:

```text
<out>/<course-name>/第N讲/transcript.txt
```

when `<out>` was already `.../transcripts/<course-name>/第N讲`. After download, search under the requested output directory for `transcript.txt`; if it is nested, copy the largest/latest transcript back to the canonical path:

```text
D:/Course/<course>/transcripts/<course-name>/第N讲/transcript.txt
```

Then verify character counts before generating review notes.

## Good batch pattern for late-course updates

When the guide is updated with new lecture mappings and local PDFs are already in topic folders:

1. Read `guide.md` and identify new hand-to-lecture rows.
2. Copy `topic-folder/handN.pdf` into `materials/handN.pdf` if missing.
3. Extract `materials/handN.txt` using PyMuPDF and verify non-trivial size/page count.
4. Use `list-courses` to resolve the course ID, then `list-videos` to match `第N讲` videos.
5. Download subtitles and normalize them to canonical transcript paths.
6. Write review notes in small batches, preserving the user's high-detail Chinese exam-review style.
7. Rebuild `reviews/INDEX.md` from actual filesystem state and read it back before reporting completion.
