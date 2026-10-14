import re

_SPACES_AND_ZWNJ = re.compile(r"[\s\u200c]+")
_WHITESPACE = re.compile(r"\s+")
_HTML_TAGS = re.compile(r"<[^>]*>")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def normalize_search(text: str) -> str:
    """Same rules as the frontend: ي->ی, ك->ک, strip spaces and ZWNJ, lowercase."""
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = _SPACES_AND_ZWNJ.sub("", text)
    return text.lower()


def slugify_tag(name: str) -> str:
    return _WHITESPACE.sub("-", name.strip())


def clean_user_text(text: str) -> str:
    """تگ‌های HTML و کاراکترهای کنترلی را از متن کاربر حذف می‌کند."""
    text = _HTML_TAGS.sub("", text)
    text = _CONTROL_CHARS.sub("", text)
    return text.strip()