from scripts.video_client import SJTUVideoClient, SubtitleItem, format_srt_time


def test_format_srt_time():
    assert format_srt_time(3_661_234) == "01:01:01,234"


def test_subtitle_to_srt_uses_next_start_as_end_except_last_item():
    items = [
        SubtitleItem(bg=0, ed=900, res="大家好"),
        SubtitleItem(bg=1200, ed=2500, res="今天讲系统"),
    ]
    assert SJTUVideoClient.subtitle_to_srt(items) == (
        "1\n00:00:00,000 --> 00:00:01,200\n大家好\n\n"
        "2\n00:00:01,200 --> 00:00:02,500\n今天讲系统\n"
    )


def test_subtitle_to_text():
    items = [SubtitleItem(bg=65_000, ed=66_000, res="一分钟后")]
    assert SJTUVideoClient.subtitle_to_text(items) == "[01:05] 一分钟后"
