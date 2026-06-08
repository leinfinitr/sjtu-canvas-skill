# Local rewrite and INDEX refresh workflow

Use this when the course workspace already contains downloaded PDFs, extracted `.txt` files, transcripts, and older review notes, and the task is to upgrade note quality or finish the remaining hands without re-querying Canvas.

## Trigger conditions

- The user already has a local workspace like `D:/Course/ADA`.
- Materials and transcripts are present under `materials/` and `transcripts/`.
- Existing review notes exist under `reviews/` but are too short, inconsistent, or mixed-quality.
- The user wants a high-quality final pass and/or a refreshed `INDEX.md`.

## Workflow

1. Read `guide.md` first and treat it as the authoritative hand-to-lecture mapping.
2. Audit local state before touching anything:
   - `materials/handN.pdf`
   - `materials/handN.txt`
   - `transcripts/<course>/<第K讲>/transcript.txt`
   - `reviews/handN_review_note.md`
3. Prefer local sources over fresh Canvas calls when the needed files are already present and readable.
4. Rewrite notes in small verified batches, not a one-shot mass rewrite. Good batch sizes are 1 hand for calibration, then 2-3 hands at a time.
5. For each rewritten note, explicitly combine:
   - PDF structure and theorem order
   - transcript emphasis / teacher intuition
   - exam-oriented explanation, pitfalls, proof templates, and self-test questions
6. When a hand spans multiple lectures, keep the note grouped by the guide mapping (for example `hand15 -> 25, 26, 27, 28`) instead of forcing one file per lecture.
7. After the content pass, rebuild `reviews/INDEX.md` from actual filesystem state, not memory:
   - list every generated `hand*_review_note.md`
   - show mapped lectures from `guide.md`
   - include transcript availability / missing lecture numbers
   - include real file paths and current file sizes
8. Verify by reading back the rewritten note header / major sections and the new INDEX before claiming completion.

## Quality bar

The target is not a bullet summary. Match the style of a polished Chinese exam-review handout:

- explain what the lecture group is really about
- connect related problems into one narrative
- state what each reduction / theorem / algorithm is doing and why
- include common wrong directions and proof pitfalls
- include self-test questions with short answer hints

## Pitfalls

- Do not regenerate from raw transcripts only when `materials/handN.txt` already provides the structural backbone.
- Do not leave old INDEX entries with stale file sizes after rewriting notes.
- Do not claim transcript-backed coverage for lectures whose `transcript.txt` is missing; list the missing lecture numbers in INDEX.
- If old notes exist, overwrite them only after confirming the new note is materially better and aligned with the guide mapping.
