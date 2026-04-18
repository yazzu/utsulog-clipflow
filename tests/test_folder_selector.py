import json
import pytest
from pathlib import Path
from clipflow.folder_selector import get_oldest_folder


def test_get_oldest_folder_returns_oldest(tmp_path):
    older = tmp_path / "20260410_1200_abc123"
    newer = tmp_path / "20260412_2233_3hqPAjxCLDs"
    older.mkdir()
    newer.mkdir()
    result = get_oldest_folder(str(tmp_path))
    assert result == older


def test_get_oldest_folder_single_folder(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    result = get_oldest_folder(str(tmp_path))
    assert result == folder


def test_get_oldest_folder_empty_dir(tmp_path):
    result = get_oldest_folder(str(tmp_path))
    assert result is None


def test_get_oldest_folder_nonexistent_dir():
    result = get_oldest_folder("/nonexistent/path/that/does/not/exist")
    assert result is None


from clipflow.folder_selector import get_next_file


def _write_post_metadata(folder: Path, records: list) -> None:
    with open(folder / "post_metadata.ndjson", "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def test_get_next_file_returns_pending_by_highlight_no(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    _write_post_metadata(folder, [
        {"file": "highlight_002_ja.mp4", "lang": "jp", "highlight_no": 2, "status": "pending", "yt_id": "", "tt_id": ""},
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    result = get_next_file(folder, "jp")
    assert result["file"] == "highlight_001_ja.mp4"


def test_get_next_file_filters_by_lang(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    _write_post_metadata(folder, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "status": "pending", "yt_id": "", "tt_id": ""},
        {"file": "highlight_001_en.mp4", "lang": "en", "highlight_no": 1, "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    result = get_next_file(folder, "en")
    assert result["file"] == "highlight_001_en.mp4"


def test_get_next_file_prefers_pending_over_partial(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    _write_post_metadata(folder, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "status": "partial", "yt_id": "abc", "tt_id": ""},
        {"file": "highlight_002_ja.mp4", "lang": "jp", "highlight_no": 2, "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    result = get_next_file(folder, "jp")
    assert result["file"] == "highlight_002_ja.mp4"


def test_get_next_file_returns_partial_when_no_pending(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    _write_post_metadata(folder, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "status": "posted", "yt_id": "x", "tt_id": "y"},
        {"file": "highlight_002_ja.mp4", "lang": "jp", "highlight_no": 2, "status": "partial", "yt_id": "abc", "tt_id": ""},
    ])
    result = get_next_file(folder, "jp")
    assert result["file"] == "highlight_002_ja.mp4"


def test_get_next_file_returns_none_when_all_posted(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    _write_post_metadata(folder, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "status": "posted", "yt_id": "x", "tt_id": "y"},
    ])
    result = get_next_file(folder, "jp")
    assert result is None


def test_get_next_file_returns_none_for_unknown_lang(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    _write_post_metadata(folder, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    result = get_next_file(folder, "en")
    assert result is None
