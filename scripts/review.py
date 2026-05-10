from __future__ import annotations

from typing import Iterable

from .video_client import SubtitleItem, format_text_time


def build_review_markdown(
    *,
    course_id: int,
    video_id: str,
    video_name: str,
    cour_id: int | None,
    transcript_text: str,
    subtitle_items: Iterable[SubtitleItem] = (),
) -> str:
    """Build a local review note from transcript text.

    The CLI intentionally does not call an external LLM. Hermes can later read this
    Markdown/transcript and generate a deeper summary in-chat.
    """
    items = list(subtitle_items)
    preview_points = []
    for item in items[:12]:
        preview_points.append(f"- [{format_text_time(item.bg)}] {item.res}")
    preview = "\n".join(preview_points) if preview_points else "- 暂无可用字幕片段。"

    return f"""# 课程回顾：{video_name}

## 基本信息
- Canvas Course ID: {course_id}
- Video ID: {video_id}
- Video Platform Course ID: {cour_id if cour_id is not None else 'N/A'}

## 快速回顾
本文件由 SJTU Canvas 课堂视频字幕自动生成。当前 CLI 先保存结构化字幕与复习模板；如需更深入总结，可让 Hermes 基于下方 transcript 继续提炼重点、概念和自测题。

## 开头片段
{preview}

## 自测问题
- 本节课主要解决了什么问题？
- 老师给出的关键定义、公式或系统设计点是什么？
- 哪些时间点需要回看？

## 完整字幕

```text
{transcript_text}
```
"""
