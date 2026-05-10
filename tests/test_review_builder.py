from scripts.review_builder import build_study_note


def test_build_study_note_combines_material_and_transcript():
    note = build_study_note(
        course_name="算法设计与分析",
        lesson_name="第28讲",
        material_name="第28讲.pdf",
        material_text="Slide 1: Hamilton Cycle\nSlide 2: reduction",
        transcript_text="[05:35] 新的一类问题叫做序列问题",
    )
    assert "# 算法设计与分析 第28讲 复习材料" in note
    assert "第28讲.pdf" in note
    assert "Hamilton Cycle" in note
    assert "[05:35]" in note
