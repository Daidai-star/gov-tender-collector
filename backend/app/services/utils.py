import hashlib
from urllib.parse import urljoin


def sha256_text(raw: str) -> str:
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def normalize_url(base_url: str, maybe_relative_url: str) -> str:
    return urljoin(base_url, maybe_relative_url)
