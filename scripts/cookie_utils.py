import re
from http.cookies import SimpleCookie
from typing import Dict

_ILLEGAL_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def parse_cookie_string(cookie_string: str) -> Dict[str, str]:
    """Parse a browser Cookie header string into a requests-compatible dict."""
    cookies: Dict[str, str] = {}
    if not cookie_string:
        return cookies

    for part in cookie_string.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        name = name.strip()
        if not name:
            continue
        cookies[name] = value.strip()
    return cookies


def mask_cookie_string(cookie_string: str) -> str:
    """Return a log-safe representation of a Cookie header."""
    masked = []
    for name in parse_cookie_string(cookie_string):
        masked.append(f"{name}=***")
    return "; ".join(masked)


def sanitize_filename(name: str, fallback: str = "untitled") -> str:
    """Make a string safe as one path component on common filesystems."""
    cleaned = _ILLEGAL_FILENAME_CHARS.sub("_", name or "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip(" .")
    return cleaned or fallback
