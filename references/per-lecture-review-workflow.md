# Per-lecture review material workflow

Use this when the user asks to generate review material for multiple `lecN` entries from a local course workspace and SJTU Canvas subtitles.

## Key workflow

1. Treat `guide.md` as authoritative for `lecN -> classroom lecture numbers` mapping.
2. Generate one output file per `lecN` / course day unless the user explicitly asks for a combined note.
   - Example: `reviews/lec1_review_material.md`, `reviews/lec2_review_material.md`, `reviews/lec3_review_material.md`.
   - A combined `lec1-3_review_material.md` can be retained as history, but should not be the main deliverable when the user asks for daily materials.
3. Use local course materials as the structural backbone:
   - PDFs/PPTX under the workspace root or `materials_text/` extracted text.
   - Keep each note scoped to its mapped lecture numbers.
4. Use SJTU Canvas subtitles to add teacher emphasis and intuition, but do not over-trust noisy transcript fragments.
5. Skip student/team presentation segments:
   - Look for cues like `小组`, `汇报`, `presentation`, `论文`, student-report tone, or paper-system slide sections.
   - Explicitly record the skipped range in the affected note.
6. Write or refresh `reviews/INDEX.md` from actual generated files, including mapping, source files, transcript availability, and skipped-presentation caveats.
7. Verify with line counts and a quick header/key-marker readback before reporting completion.

## Credential and path pattern on Windows Git Bash

- The `sjtu-canvas-skill` installed skill directory may contain the working `.env` even when the course workspace does not.
- For Canvas video/subtitle commands, run the CLI from the skill directory so python-dotenv loads that `.env`.
- When a command running under `uv` / Windows Python needs to write into the course workspace, prefer native Windows paths such as `D:\Course\AdvancedDistributedSystem\videos_90691.json` over MSYS paths like `/d/Course/...`; Windows Python may not resolve MSYS paths inside `Path(...)`.
- Do not print cookie values. It is safe to report only whether keys like `OC_COOKIE` and `TOKEN` are present.

## Output quality

Each per-lecture note should include:

- Scope and source note: mapped classroom lectures, material path, subtitle coverage.
- One-sentence lecture theme.
- Coherent explanation of definitions and motivations.
- Teacher-emphasis details from subtitles when available.
- Common pitfalls and exam-style proof/judgment templates.
- Self-test questions with short answers.
- A clear note about skipped student presentation content when applicable.
