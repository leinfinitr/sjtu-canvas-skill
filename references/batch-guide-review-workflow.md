# Batch lecture-review workflow from `guide.md`

Use this when the user provides a course-level guide mapping material PDFs to lecture video numbers and asks for all review materials.

## Workflow

1. Locate and read the guide. Do not assume it is under the skill directory; the user may keep it in the current course workspace (for example `D:/Course/ADA/guide.md`). If not found, ask for the path or search the user-provided workspace.
2. Parse mappings like `hand16 | 29, 30` into `{material: hand16.pdf, lectures: [29, 30]}`.
3. Refresh or create course caches once, then reuse them for all batches:

```bash
cd "$LOCALAPPDATA/hermes/skills/sjtu-canvas-skill"
uv run main --json list-files <course_id> > "<workspace>/cache/files_<course_id>.json"
uv run main --json list-videos <course_id> > "<workspace>/cache/videos_<course_id>.json"
```

4. For each material group:
   - Prefer `handN.pdf` over `algoN.pdf` when the guide says `handN`.
   - Download PDFs into `<workspace>/materials/` with `download-file` using the fresh `url` from `list-files`.
   - Extract PDF text to `<workspace>/materials/handN.txt` with PyMuPDF, then verify the extracted text is non-trivial before writing the review note. If the text is suspiciously short, rerun extraction instead of summarizing from a broken export.
   - Match videos by `第N讲` in `video_name` and download subtitles into `<workspace>/transcripts/`.
   - Generate `<workspace>/reviews/handN_review_note.md`.
5. When quality matters, do not one-shot all hands into shallow summaries. First produce one detailed exemplar note (or use an existing good one such as `hand16_review_note.md`) as the quality benchmark, then continue in small verified batches.
6. Create `<workspace>/reviews/INDEX.md` listing every generated note, material path, transcript status, and any missing subtitles.

## Review note shape

For each `handN_review_note.md`, aim for the detailed `hand16_review_note.md` style rather than a short template summary. Include:

- Source paths: guide, PDF, PDF text, transcripts.
- One-sentence theme.
- A "主线" section that explains what the lecture group is really about.
- Per-lecture explanations that combine the PDF with transcript emphasis, not just bullet extraction.
- Key definitions / algorithms / proof templates.
- Pitfalls and common exam mistakes.
- Self-test questions with answer hints.
- Suggested review order.
- Explicit caveats when a lecture subtitle is missing; never imply transcript-backed coverage if only the PDF was available.

## Parallelization with subagents

Only use broad subagent batching when the user explicitly wants speed over polish. If the user cares about note quality or has already complained about shallow summaries, prefer parent-session writing or very small batches (for example one hand first, then `hand2-hand4`, then the next batch) with manual verification between batches.

If you do use subagents, batch them by disjoint material ranges, e.g. `hand1-hand5`, `hand6-hand11`, `hand12-hand16`. Give each subagent full context including:

- Skill directory and required working directory.
- `course_id`.
- Guide mapping.
- Workspace root.
- Cache file locations.
- Output contract.
- No secret leakage.

Subagents may time out after doing partial work. Always perform a parent-session verification pass:

```text
expected notes = all guide materials
expected PDFs = all guide materials
expected transcripts = all lecture numbers, except videos with no platform subtitles
```

Then fill gaps in the parent session or with smaller follow-up subagents. Do not treat a subagent timeout as total failure; inspect the output directories first.

## Pitfalls

- Some lectures may have no platform subtitle even when videos exist. Record this in the note and index instead of inventing transcript content.
- Avoid shell-sourcing `.env` because Canvas cookies can contain quotes, spaces, and semicolons. Let the Python CLI / python-dotenv load `.env`.
- On Windows Git Bash, run commands from the skill directory and use quoted paths for course workspaces such as `D:/Course/ADA`.
- If using `execute_code` to call terminal commands, inspect stdout and verify filesystem effects; nested shell quoting can silently prevent intended work from running.
