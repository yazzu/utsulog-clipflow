import json
from pathlib import Path


def get_oldest_folder(pending_dir: str) -> Path | None:
    base = Path(pending_dir)
    if not base.exists():
        return None
    folders = sorted(
        [f for f in base.iterdir() if f.is_dir()],
        key=lambda f: f.name,
    )
    return folders[0] if folders else None
