import json
from pathlib import Path


def read_post_metadata(folder: Path) -> list:
    path = folder / "post_metadata.ndjson"
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_post_metadata(folder: Path, records: list) -> None:
    path = folder / "post_metadata.ndjson"
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
