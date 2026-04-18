import json
import pytest
from pathlib import Path
from clipflow.metadata import read_post_metadata, write_post_metadata

FIXTURE_FOLDER = Path("tests/fixtures/20260412_2233_3hqPAjxCLDs")


def test_read_post_metadata_returns_all_records():
    records = read_post_metadata(FIXTURE_FOLDER)
    assert len(records) == 6


def test_read_post_metadata_fields():
    records = read_post_metadata(FIXTURE_FOLDER)
    first = records[0]
    assert first["file"] == "highlight_001_ja.mp4"
    assert first["lang"] == "jp"
    assert first["highlight_no"] == 1
    assert first["status"] == "pending"


def test_write_post_metadata_roundtrip(tmp_path):
    original = read_post_metadata(FIXTURE_FOLDER)
    write_post_metadata(tmp_path, original)

    written = read_post_metadata(tmp_path)
    assert len(written) == len(original)
    assert written[0]["file"] == original[0]["file"]
    assert written[0]["title"] == original[0]["title"]


def test_write_post_metadata_preserves_japanese(tmp_path):
    records = [{"file": "a.mp4", "title": "日本語テスト", "lang": "jp"}]
    write_post_metadata(tmp_path, records)
    result = read_post_metadata(tmp_path)
    assert result[0]["title"] == "日本語テスト"


from clipflow.metadata import update_post_metadata


def _make_folder(tmp_path: Path, records: list) -> Path:
    write_post_metadata(tmp_path, records)
    return tmp_path


def test_update_post_metadata_both_success(tmp_path):
    _make_folder(tmp_path, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1,
         "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    update_post_metadata(tmp_path, "highlight_001_ja.mp4", yt_id="YT123", tt_id="TT456")
    result = read_post_metadata(tmp_path)
    assert result[0]["status"] == "posted"
    assert result[0]["yt_id"] == "YT123"
    assert result[0]["tt_id"] == "TT456"


def test_update_post_metadata_yt_only(tmp_path):
    _make_folder(tmp_path, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1,
         "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    update_post_metadata(tmp_path, "highlight_001_ja.mp4", yt_id="YT123", tt_id=None)
    result = read_post_metadata(tmp_path)
    assert result[0]["status"] == "partial"
    assert result[0]["yt_id"] == "YT123"
    assert result[0]["tt_id"] == ""


def test_update_post_metadata_tt_only(tmp_path):
    _make_folder(tmp_path, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1,
         "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    update_post_metadata(tmp_path, "highlight_001_ja.mp4", yt_id=None, tt_id="TT456")
    result = read_post_metadata(tmp_path)
    assert result[0]["status"] == "partial"
    assert result[0]["yt_id"] == ""
    assert result[0]["tt_id"] == "TT456"


def test_update_post_metadata_both_fail(tmp_path):
    _make_folder(tmp_path, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1,
         "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    update_post_metadata(tmp_path, "highlight_001_ja.mp4", yt_id=None, tt_id=None)
    result = read_post_metadata(tmp_path)
    assert result[0]["status"] == "pending"


def test_update_post_metadata_partial_completes(tmp_path):
    """既に yt_id がある partial レコードに tt_id を追加すると posted になる"""
    _make_folder(tmp_path, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1,
         "status": "partial", "yt_id": "YT123", "tt_id": ""},
    ])
    update_post_metadata(tmp_path, "highlight_001_ja.mp4", yt_id=None, tt_id="TT456")
    result = read_post_metadata(tmp_path)
    assert result[0]["status"] == "posted"
    assert result[0]["yt_id"] == "YT123"
    assert result[0]["tt_id"] == "TT456"


def test_update_post_metadata_only_updates_target_file(tmp_path):
    _make_folder(tmp_path, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1,
         "status": "pending", "yt_id": "", "tt_id": ""},
        {"file": "highlight_002_ja.mp4", "lang": "jp", "highlight_no": 2,
         "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    update_post_metadata(tmp_path, "highlight_001_ja.mp4", yt_id="YT123", tt_id="TT456")
    result = read_post_metadata(tmp_path)
    assert result[1]["status"] == "pending"


from clipflow.metadata import update_ab_metadata


def _write_ab_metadata(folder: Path, records: list) -> None:
    path = folder / "ab_metadata.ndjson"
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _read_ab_metadata(folder: Path) -> list:
    path = folder / "ab_metadata.ndjson"
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def test_update_ab_metadata_adds_yt_id(tmp_path):
    _write_ab_metadata(tmp_path, [
        {"highlight_id": "highlight_001", "language": "ja", "video_id": None, "yt_id": None, "tt_id": None},
    ])
    update_ab_metadata(tmp_path, "highlight_001", "jp", yt_id="YT123", tt_id=None)
    result = _read_ab_metadata(tmp_path)
    assert result[0]["yt_id"] == "YT123"
    assert result[0]["tt_id"] is None


def test_update_ab_metadata_adds_tt_id(tmp_path):
    _write_ab_metadata(tmp_path, [
        {"highlight_id": "highlight_001", "language": "ja", "video_id": None, "yt_id": None, "tt_id": None},
    ])
    update_ab_metadata(tmp_path, "highlight_001", "jp", yt_id=None, tt_id="TT456")
    result = _read_ab_metadata(tmp_path)
    assert result[0]["tt_id"] == "TT456"


def test_update_ab_metadata_maps_jp_to_ja(tmp_path):
    _write_ab_metadata(tmp_path, [
        {"highlight_id": "highlight_001", "language": "ja", "video_id": None, "yt_id": None, "tt_id": None},
        {"highlight_id": "highlight_001", "language": "en", "video_id": None, "yt_id": None, "tt_id": None},
    ])
    update_ab_metadata(tmp_path, "highlight_001", "jp", yt_id="YT123", tt_id=None)
    result = _read_ab_metadata(tmp_path)
    assert result[0]["yt_id"] == "YT123"   # language="ja" のレコードが更新される
    assert result[1]["yt_id"] is None       # language="en" は変更なし


def test_update_ab_metadata_en_lang(tmp_path):
    _write_ab_metadata(tmp_path, [
        {"highlight_id": "highlight_001", "language": "en", "video_id": None, "yt_id": None, "tt_id": None},
    ])
    update_ab_metadata(tmp_path, "highlight_001", "en", yt_id="YT999", tt_id="TT888")
    result = _read_ab_metadata(tmp_path)
    assert result[0]["yt_id"] == "YT999"
    assert result[0]["tt_id"] == "TT888"


def test_update_ab_metadata_does_not_overwrite_existing_video_id(tmp_path):
    _write_ab_metadata(tmp_path, [
        {"highlight_id": "highlight_001", "language": "ja", "video_id": "ORIGINAL", "yt_id": None, "tt_id": None},
    ])
    update_ab_metadata(tmp_path, "highlight_001", "jp", yt_id="YT123", tt_id=None)
    result = _read_ab_metadata(tmp_path)
    assert result[0]["video_id"] == "ORIGINAL"  # 既存フィールドは変更しない
