---
name: sjtu-canvas-skill
description: Interacts with the SJTU Canvas API to manage courses, assignments, and files. Use this skill for tasks related to SJTU Canvas.
---

# SJTU Canvas Skill

This skill provides a command-line interface (CLI) to interact with the Shanghai Jiao Tong University (SJTU) Canvas Learning Management System. It allows you to access course information, manage assignments, and handle files.

## Configuration

Configuration is handled via CLI options or environment variables. By default use `.env` file in this skill directory to store your credentials.

### Environment Variables

- `TOKEN`: Your Canvas API token.
- `BASE_URL`: The base URL for the Canvas instance (defaults to `https://oc.sjtu.edu.cn`).

### CLI Options

- `--token`: Your Canvas API token.
- `--base-url`: The base URL for the Canvas instance.
- `--json`: Output raw JSON instead of formatted tables (ideal for agent usage).

### How to get an API Token

1.  Log in to your SJTU Canvas account.
2.  Go to **Account** > **Settings**.
3.  Scroll down to the **Approved Integrations** section.
4.  Click **+ New Access Token**.
5.  Give it a purpose (e.g., "Gemini CLI Agent") and an expiration date.
6.  Click **Generate Token**.
7.  **Important**: Copy the generated token immediately. You will not be able to see it again.

### Local installation inside Hermes skill directory

If installed from a direct raw `SKILL.md` URL, Hermes may install only `SKILL.md` and omit the repo's CLI implementation files. For this skill, clone the repo and copy at least `references/`, `scripts/`, `pyproject.toml`, `uv.lock`, and `README.md` into the installed skill directory, then verify from that directory:

```bash
git clone https://github.com/leinfinitr/sjtu-canvas-skill.git /tmp/sjtu-canvas-skill
SKILL_DIR="$LOCALAPPDATA/hermes/skills/sjtu-canvas-skill"  # Windows git-bash example
cp -R /tmp/sjtu-canvas-skill/references "$SKILL_DIR/"
cp -R /tmp/sjtu-canvas-skill/scripts "$SKILL_DIR/"
cp /tmp/sjtu-canvas-skill/pyproject.toml /tmp/sjtu-canvas-skill/uv.lock /tmp/sjtu-canvas-skill/README.md "$SKILL_DIR/"
cd "$SKILL_DIR"
uv run main --help
```

On Windows Hermes terminal uses git-bash/MSYS; `$LOCALAPPDATA/hermes/skills/sjtu-canvas-skill` works, and `/tmp/...` may resolve under the Windows temp directory.

Credential behavior: if `TOKEN` is not set, `uv run main --json list-courses` prompts interactively for the Canvas token and can hang in non-interactive tool calls. Before running Canvas queries, check for `TOKEN`/`BASE_URL`/`OC_COOKIE` in `hermes/skills/sjtu-canvas-skill/.env` or pass `--token` explicitly. Use `TOKEN` for Canvas API course/files/assignments; use `OC_COOKIE` additionally for classroom video/subtitle workflows.

See `references/local-install-and-dns.md` for local install details, non-interactive credential checks, the Windows aiohttp/aiodns DNS workaround, and how to interpret `list-videos` failures when course-file workflows still work.

See `references/review-workflow.md` for the lecture-review workflow: resolve course/video/material IDs, download Canvas files, download subtitles, extract PDF text, combine sources into a review note, and handle stale-cookie or missing-video pitfalls.

See `references/batch-guide-review-workflow.md` when the user provides a `guide.md` mapping many PDFs to lecture numbers and asks for all course review materials. It covers cache reuse, subagent batching, gap-filling after timeouts, transcript-missing handling, and `INDEX.md` generation.

See `references/incremental-review-updates.md` when a review note already exists and a renewed cookie or later Canvas update makes a previously missing lecture/video/subtitle available; patch the existing note and remove stale caveats rather than creating a competing note.

See `references/early-lecture-subtitle-review.md` when local lecture PDFs/PPTX are already present and `guide.md` maps `lecN` files to classroom-video lecture numbers; it covers combining teacher subtitles with slide structure, marking missing/noisy subtitles, and skipping later student/team-report sections.

See `references/local-rewrite-and-index-refresh.md` when the workspace already has local PDFs, extracted text, transcripts, and older review notes, and the task is to do a final high-quality rewrite / gap-fill pass plus rebuild `reviews/INDEX.md` from actual filesystem state.

See `references/per-lecture-review-workflow.md` when the user asks for review materials for several local `lecN` course days and expects one file per day/lecture mapping. It covers using `guide.md`, loading `.env` from the skill directory, Windows path pitfalls, skipping student presentation segments, generating per-lecture notes, and refreshing `reviews/INDEX.md`.

See `references/windows-local-review-pitfalls.md` for Windows Git Bash/local-workspace pitfalls: verifying the actual tool backend after `/reload`, avoiding native-Python `/tmp` mismatches, normalizing nested downloaded subtitle paths, and the proven late-course update pattern.

### Review-note quality and batching expectations

For this user's SJTU Canvas review workflow, default to:

- High-detail Chinese review notes, not brief template summaries.
- A structure that explains definitions, intuition, proof logic, algorithmic motivation, complexity analysis, pitfalls, and self-test questions.
- Integrating PDF slides with transcript evidence, but rewriting into clean study material rather than dumping raw extraction.
- Small verified batches (for example 1-2 hands / lectures at a time) instead of one-shot mass generation across the whole course.

When rewriting or upgrading existing review notes:

- Treat concise or skeletal notes as insufficient unless the user explicitly asks for brevity.
- Prefer the quality level of a polished exam-review handout: coherent narrative, explicit theorem dependencies, and concrete "why" explanations.
- After each small batch, verify the generated files before claiming completion.

---

### **`list-courses`**

Lists all active courses for the current user.

**Command:**

```bash
uv run main list-courses
```

---

### **`list-assignments <course_id>`**

Lists all assignments for a given course.

**Parameters:**

- `course_id`: The ID of the course.

**Command:**

```bash
uv run main list-assignments <course_id>
```

---

### **`submit <course_id> <assignment_id> <files...>`**

Submits one or more files for an assignment.

**Parameters:**

- `course_id`: The ID of the course.
- `assignment_id`: The ID of the assignment.
- `files`: One or more paths to the files to submit.

**Options:**

- `--comment <comment>`: Add a text comment to the submission.

**Command:**

```bash
uv run main submit <course_id> <assignment_id> <file1> <file2> --comment "My submission"
```

---

### **`get-me`**

Gets the profile of the current user.

**Command:**

```bash
uv run main get-me
```

---

### **`list-files <course_id>`**

Lists all files for a given course.

**Parameters:**

- `course_id`: The ID of the course.

**Command:**

```bash
uv run main list-files <course_id>
```

---

### **`list-folders <course_id>`**

Lists all folders for a given course.

**Parameters:**

- `course_id`: The ID of the course.

**Command:**

```bash
uv run main list-folders <course_id>
```

---

### **`download-file <url>`**

Downloads a file from a specific URL.

**Parameters:**

- `url`: The URL of the file to download.

**Options:**

- `--path <path>`: The directory to save the file in (defaults to the current directory).

**Command:**

```bash
uv run main download-file <file_url> --path /path/to/save
```

---

### **`list-videos <course_id>`**

Lists classroom videos for a Canvas course. This uses SJTU's classroom video LTI platform and requires an authenticated `OC_COOKIE` browser cookie in addition to the Canvas API token.

**Environment:**

- `OC_COOKIE`: Browser Cookie header for an authenticated `oc.sjtu.edu.cn` session. Do not log or share it.

**Command:**

```bash
uv run main --json list-videos <course_id>
```

---

### **`download-subtitle <course_id>`**

Downloads platform-generated subtitles for a specific classroom video and saves `transcript.srt`, `transcript.txt`, `metadata.json`, and `review.md` locally.

**Options:**

- `--video-id <video_id>`: Video ID from `list-videos`.
- `--out <dir>`: Output directory, defaults to `./reviews`.

**Command:**

```bash
uv run main download-subtitle <course_id> --video-id <video_id> --out ./reviews
```

---

### **`review-video <course_id>`**

Creates a local transcript from platform subtitles for a classroom video.

**Command:**

```bash
uv run main review-video <course_id> --video-id <video_id> --out ./reviews
```

---

### **`study-note <course_id>`**

Recommended review workflow. Combines a local course material file (PPTX/PDF/Markdown/text) with the corresponding classroom video transcript, and writes an agent-ready `study_note.md` plus `transcript.txt` and `metadata.json`.

**Workspace convention:**

```text
course-workspace/
  .env                  # contains OC_COOKIE=...
  materials/            # PPT/PDF/homework/course files, any subdirectory layout is OK
  reviews/              # generated by this command
```

**Command:**

```bash
uv run main study-note <course_id> \
  --video-id <video_id> \
  --material "第28讲 Hamilton" \
  --workspace /path/to/course-workspace
```

If the requested material is missing, first download course files with `list-files` / `download-file`, or place the PPT/PDF in the workspace manually.

---

When users provide a **Chinese course name** instead of a numeric `course_id`, always resolve the course ID first, then run downstream commands.

### Workflow A: Chinese Course Name -> Course ID -> Course Queries

1. List courses in JSON mode:

```bash
uv run main --json list-courses
```

2. Find the target course by name (exact match or contains match), then extract its `id`.

3. Use that `course_id` for follow-up operations, for example:

```bash
uv run main list-assignments <course_id>
uv run main list-folders <course_id>
uv run main list-files <course_id>
```

Important:

- Never guess `course_id` from the course name.
- If multiple courses match the same Chinese name, ask the user to confirm by showing candidate IDs and term names.

### Workflow B: Course ID -> List Files -> Download URL -> Download File

For file downloads, do not call `download-file` directly unless you already have a valid file URL.

1. Resolve `course_id` first (use Workflow A if needed).

2. List files for that course:

```bash
uv run main --json list-files <course_id>
```

3. From the returned file list, select the target file and read its `url` field.

4. Download using the URL:

```bash
uv run main download-file "<file_url>" --path ./downloads
```

Important:

- The download URL is usually time-limited; fetch and use it promptly.
- If download fails due to expired signature, re-run `list-files` to obtain a fresh URL and retry.
