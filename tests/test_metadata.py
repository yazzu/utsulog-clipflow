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
