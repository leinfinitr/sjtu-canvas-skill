import json
import os
from pathlib import Path

import pytest
from asyncclick.testing import CliRunner

from scripts.main import cli


@pytest.mark.asyncio
async def test_list_videos_requires_oc_cookie(monkeypatch):
    monkeypatch.delenv("OC_COOKIE", raising=False)
    runner = CliRunner()
    result = await runner.invoke(cli, ["--token", "dummy", "--json", "list-videos", "123"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "error"
    assert "OC_COOKIE" in payload["message"]


def test_write_video_review_outputs_transcript_only(tmp_path):
    from scripts.main import write_video_review_files
    from scripts.video_client import SubtitleItem

    files = write_video_review_files(
        out_dir=tmp_path,
        course_name="课程/A",
        video_name="第1讲:Intro",
        course_id=1,
        video_id="v1",
        cour_id=2,
        srt="1\n00:00:00,000 --> 00:00:01,000\n你好\n",
        text="[00:00] 你好",
        subtitle_items=[SubtitleItem(bg=0, ed=1000, res="你好")],
        metadata={"x": 1},
    )
    for key in ["txt", "metadata"]:
        assert Path(files[key]).exists()
    assert "srt" not in files
    assert "review" not in files
    assert "课程_A" in files["txt"]
