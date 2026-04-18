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
