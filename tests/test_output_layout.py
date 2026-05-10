from pathlib import Path

from scripts.main import derive_course_lesson_names, write_transcript_files
from scripts.video_client import SubtitleItem


def test_derive_course_lesson_names_from_graduate_video_title():
    course, lesson = derive_course_lesson_names("算法设计与分析(研)(第27讲)")
    assert course == "算法设计与分析"
    assert lesson == "第27讲"


def test_write_transcript_files_uses_course_and_lesson_dirs_only(tmp_path):
    files = write_transcript_files(
        out_dir=tmp_path,
        course_name="算法设计与分析",
        lesson_name="第27讲",
        course_id=90690,
        video_id="abc==",
        cour_id=123,
        text="[00:00] 你好",
        subtitle_items=[SubtitleItem(bg=0, ed=1000, res="你好")],
        metadata={"x": 1},
    )
    assert Path(files["txt"]).exists()
    assert Path(files["metadata"]).exists()
    assert "算法设计与分析/第27讲" in files["txt"]
    assert "srt" not in files
    assert "review" not in files
    assert not (tmp_path / "算法设计与分析" / "第27讲" / "transcript.srt").exists()
    assert not (tmp_path / "算法设计与分析" / "第27讲" / "review.md").exists()
