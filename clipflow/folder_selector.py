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


def get_next_file(folder: Path, lang: str) -> dict | None:
    metadata_path = folder / "post_metadata.ndjson"
    records = []
    with open(metadata_path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    candidates = [
        r for r in records
        if r["lang"] == lang and r["status"] in ("pending", "partial")
    ]
    if not candidates:
        return None

    candidates.sort(key=lambda r: (0 if r["status"] == "pending" else 1, r["highlight_no"]))
    return candidates[0]
