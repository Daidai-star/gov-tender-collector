from pathlib import Path

from app.core.config import get_settings
from app.services.utils import sha256_bytes

settings = get_settings()


def ensure_storage_root() -> Path:
    root = settings.resolved_storage_root
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_attachment(notice_id: int, file_name: str, content: bytes) -> tuple[str, int, str]:
    root = ensure_storage_root()
    folder = root / str(notice_id)
    folder.mkdir(parents=True, exist_ok=True)
    safe_name = file_name.replace('/', '_').replace('\\', '_')
    if not safe_name:
        safe_name = 'attachment.bin'
    file_path = folder / safe_name
    file_path.write_bytes(content)
    digest = sha256_bytes(content)
    return str(file_path), len(content), digest
