import pytest

from scripts.cookie_utils import mask_cookie_string, parse_cookie_string, sanitize_filename


def test_parse_cookie_string_basic():
    assert parse_cookie_string("a=1; b=hello") == {"a": "1", "b": "hello"}


def test_parse_cookie_string_ignores_empty_and_invalid_parts():
    assert parse_cookie_string("a=1; ; invalid; b=2;") == {"a": "1", "b": "2"}


def test_parse_cookie_string_preserves_equals_in_value():
    assert parse_cookie_string("token=a=b=c; x=1") == {"token": "a=b=c", "x": "1"}


def test_mask_cookie_string_hides_values():
    masked = mask_cookie_string("JSESSIONID=abcdef; other=123456")
    assert "abcdef" not in masked
    assert "123456" not in masked
    assert "JSESSIONID=" in masked
    assert "other=" in masked


def test_sanitize_filename_removes_illegal_path_chars():
    assert sanitize_filename('A/B:C*D?E"F<G>H|') == "A_B_C_D_E_F_G_H_"


def test_sanitize_filename_has_fallback():
    assert sanitize_filename("   ") == "untitled"
