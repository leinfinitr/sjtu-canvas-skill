from pathlib import Path

from scripts.materials import extract_material_text, find_material_file


def test_find_material_file_by_keyword(tmp_path):
    target = tmp_path / "算法设计与分析-第28讲-Hamilton.pdf"
    target.write_text("dummy", encoding="utf-8")
    assert find_material_file(tmp_path, "第28讲 Hamilton") == target


def test_extract_material_text_from_plain_markdown(tmp_path):
    p = tmp_path / "lecture.md"
    p.write_text("# 第28讲\nHamilton Cycle", encoding="utf-8")
    result = extract_material_text(p)
    assert "Hamilton Cycle" in result.text
    assert result.path == p
