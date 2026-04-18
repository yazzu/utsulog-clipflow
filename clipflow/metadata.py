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


def update_post_metadata(
    folder: Path, file: str, yt_id: str | None, tt_id: str | None
) -> None:
    records = read_post_metadata(folder)
    for record in records:
        if record["file"] != file:
            continue
        if yt_id is not None:
            record["yt_id"] = yt_id
        if tt_id is not None:
            record["tt_id"] = tt_id
        has_yt = bool(record.get("yt_id"))
        has_tt = bool(record.get("tt_id"))
        if has_yt and has_tt:
            record["status"] = "posted"
        elif has_yt or has_tt:
            record["status"] = "partial"
        break
    write_post_metadata(folder, records)
