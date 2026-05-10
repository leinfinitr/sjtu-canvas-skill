from __future__ import annotations


def build_study_note(
    *,
    course_name: str,
    lesson_name: str,
    material_name: str,
    material_text: str,
    transcript_text: str,
) -> str:
    """Build an agent-ready study note combining course material and transcript.

    This file deliberately preserves the raw evidence. Hermes/LLM can then use it
    to produce a polished summary with citations to slides/pages and timestamps.
    """
    return f"""# {course_name} {lesson_name} 复习材料

## 使用材料
- 课程材料：{material_name}
- 课堂字幕：transcript.txt

## 如何使用
请基于下方两份材料整理复习笔记：
1. 先用课程材料确定本节课的知识结构、定义、定理、例题和证明脉络。
2. 再用课堂字幕补充老师强调的重点、易错点和解释。
3. 对每个知识点标注来源位置：材料中的页/slide附近文本，以及视频中的时间戳。

## 课程材料原文

```text
{material_text}
```

## 课堂字幕原文

```text
{transcript_text}
```
"""
