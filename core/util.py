import re
from urllib.parse import urlparse

MOS_DOMAIN = "mos-gorsud.ru"

def detect_link_type(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.endswith(MOS_DOMAIN):
        return "mos"
    if host.endswith(".sudrf.ru") or host == "sudrf.ru":
        return "sudrf"
    return "unknown"

def validate_url(url: str) -> str:
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValueError("Ссылка должна начинаться с http:// или https://")
    t = detect_link_type(url)
    if t == "unknown":
        raise ValueError("Поддерживаются только mos-gorsud.ru и *.sudrf.ru")
    return url

def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text
