# Early-lecture review with local slides plus Canvas subtitles

Use this pattern when a course workspace has local lecture PDFs/PPTX and a `guide.md` mapping lecture files to classroom-video lecture numbers, and the user asks for review material based on teacher lecture content.

## Workflow

1. Load `guide.md` first and resolve the local lecture file to classroom lecture numbers, for example `lec1 -> 1,2,3,4`.
2. Resolve the Canvas course ID via `list-courses`; do not guess from the directory name.
3. Run `list-videos <course_id>` and match `第N讲` for every lecture number from `guide.md`.
4. Download subtitles for all matched videos with `download-subtitle`; record which lecture numbers have no platform subtitle or only unusable noise.
5. Extract local material text:
   - PDFs: `pdftotext -layout` is acceptable when PyMuPDF is unavailable.
   - PPTX: parse `ppt/slides/slideN.xml` text nodes with Python stdlib `zipfile` + `xml.etree.ElementTree` when `python-pptx` is unavailable.
6. Build the review note from both sources:
   - Use slides as the structural backbone.
   - Use teacher-style transcript sections to add intuition, examples, emphasis, and warnings.
   - Mark missing or unusable subtitles explicitly instead of implying transcript coverage.
7. Detect and skip student/team-report sections:
   - Transcript signals: `汇报`, `小组`, `presentation`, `论文`, `我们组`, student-like scripted delivery.
   - Slide signals: paper/system title slides, architecture/evaluation sections after the core lecture summary, or a sudden shift to one specific paper such as `Causal+`.
   - Keep core conceptual lecture content; exclude report-specific architecture, experiments, and presentation details unless the user asks for them.
8. Verify the generated note by reading back the header, source-coverage caveat, and the section that explains skipped report content.

## Quality expectations

- Chinese, high-detail, exam-review style.
- Include definitions, contrasts, proof/judgment templates, pitfalls, and self-test questions.
- Avoid dumping raw transcript text; rewrite into coherent study material.
- Be honest about missing subtitles and noisy subtitle files.

## Example source caveat

```text
字幕覆盖情况：guide.md 显示 lec1→第1-4讲。实际成功下载第3、4讲；其中第4讲字幕几乎只有零散噪声，第1、2讲平台无字幕。因此本材料以课件为结构骨架，以可用且像老师授课的字幕补充解释。
```
