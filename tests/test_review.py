from pathlib import Path

from scripts.review import build_review_markdown
from scripts.video_client import SubtitleItem


def test_build_review_markdown_contains_metadata_and_transcript():
    md = build_review_markdown(
        course_id=123,
        video_id="v1",
        video_name="第1讲",
        cour_id=456,
        transcript_text="[00:00] 大家好",
        subtitle_items=[SubtitleItem(bg=0, ed=1000, res="大家好")],
    )
    assert "# 课程回顾：第1讲" in md
    assert "Canvas Course ID: 123" in md
    assert "Video Platform Course ID: 456" in md
    assert "[00:00] 大家好" in md
    assert "## 自测问题" in md
