import re

_SPACES_AND_ZWNJ = re.compile(r"[\s\u200c]+")


def normalize_search(text: str) -> str:
    """Same rules as the frontend: ي->ی, ك->ک, strip spaces and ZWNJ, lowercase."""
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = _SPACES_AND_ZWNJ.sub("", text)
    return text.lower()