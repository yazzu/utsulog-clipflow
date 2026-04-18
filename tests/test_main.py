import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from clipflow.main import run


@pytest.fixture
def pending_folder(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    records = [
        {
            "file": "highlight_001_ja.mp4",
            "lang": "jp",
            "highlight_no": 1,
            "title": "テスト",
            "description": "説明",
            "tags": ["tag1"],
            "categoryId": "20",
            "forKids": False,
            "status": "pending",
            "yt_id": "",
            "tt_id": "",
        }
    ]
    with open(folder / "post_metadata.ndjson", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(folder / "ab_metadata.ndjson", "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "highlight_id": "highlight_001",
            "language": "ja",
            "video_id": None,
            "yt_id": None,
            "tt_id": None,
        }, ensure_ascii=False) + "\n")
    video = folder / "highlight_001_ja.mp4"
    video.write_bytes(b"fake")
    return tmp_path, folder


def test_run_both_success_marks_posted_and_backups(pending_folder, monkeypatch):
    pending_dir, folder = pending_folder
    monkeypatch.setenv("PENDING_DIR", str(pending_dir))
    monkeypatch.setenv("S3_BUCKET", "test-bucket")
    monkeypatch.setenv("S3_PREFIX", "backup")

    with (
        patch("clipflow.main.youtube.upload", return_value="YT123") as mock_yt,
        patch("clipflow.main.tiktok.upload", return_value="TT456") as mock_tt,
        patch("clipflow.main.storage.backup_file") as mock_backup,
        patch("clipflow.main.storage.delete_file") as mock_delete,
        patch("clipflow.main.storage.cleanup_folder_if_empty") as mock_cleanup,
    ):
        run("jp")

    mock_yt.assert_called_once()
    mock_tt.assert_called_once()
    mock_backup.assert_called_once()
    mock_delete.assert_called_once()
    mock_cleanup.assert_called_once()

    from clipflow.metadata import read_post_metadata
    records = read_post_metadata(folder)
    assert records[0]["status"] == "posted"
    assert records[0]["yt_id"] == "YT123"
    assert records[0]["tt_id"] == "TT456"


def test_run_yt_fail_marks_partial_no_backup(pending_folder, monkeypatch):
    pending_dir, folder = pending_folder
    monkeypatch.setenv("PENDING_DIR", str(pending_dir))

    with (
        patch("clipflow.main.youtube.upload", side_effect=Exception("YT error")),
        patch("clipflow.main.tiktok.upload", return_value="TT456"),
        patch("clipflow.main.storage.backup_file") as mock_backup,
        patch("clipflow.main.storage.delete_file") as mock_delete,
        patch("clipflow.main.storage.cleanup_folder_if_empty") as mock_cleanup,
    ):
        run("jp")

    mock_backup.assert_not_called()
    mock_delete.assert_not_called()
    mock_cleanup.assert_not_called()

    from clipflow.metadata import read_post_metadata
    records = read_post_metadata(folder)
    assert records[0]["status"] == "partial"
    assert records[0]["yt_id"] == ""
    assert records[0]["tt_id"] == "TT456"


def test_run_both_fail_stays_pending(pending_folder, monkeypatch):
    pending_dir, folder = pending_folder
    monkeypatch.setenv("PENDING_DIR", str(pending_dir))

    with (
        patch("clipflow.main.youtube.upload", side_effect=Exception("YT error")),
        patch("clipflow.main.tiktok.upload", side_effect=Exception("TT error")),
        patch("clipflow.main.storage.backup_file") as mock_backup,
    ):
        run("jp")

    mock_backup.assert_not_called()

    from clipflow.metadata import read_post_metadata
    records = read_post_metadata(folder)
    assert records[0]["status"] == "pending"


def test_run_no_pending_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("PENDING_DIR", str(tmp_path))
    with patch("clipflow.main.youtube.upload") as mock_yt:
        run("jp")
    mock_yt.assert_not_called()


def test_run_partial_retries_missing_platform(pending_folder, monkeypatch):
    """partial レコードは欠けているプラットフォームのみ投稿する"""
    pending_dir, folder = pending_folder
    monkeypatch.setenv("PENDING_DIR", str(pending_dir))

    # yt_id が既にあり tt_id が空の partial レコードに更新
    from clipflow.metadata import read_post_metadata, write_post_metadata
    records = read_post_metadata(folder)
    records[0]["status"] = "partial"
    records[0]["yt_id"] = "YT_EXISTING"
    write_post_metadata(folder, records)

    with (
        patch("clipflow.main.youtube.upload") as mock_yt,
        patch("clipflow.main.tiktok.upload", return_value="TT456") as mock_tt,
        patch("clipflow.main.storage.backup_file"),
        patch("clipflow.main.storage.delete_file"),
        patch("clipflow.main.storage.cleanup_folder_if_empty"),
    ):
        run("jp")

    mock_yt.assert_not_called()  # yt_id が既にあるので呼ばない
    mock_tt.assert_called_once()

    updated = read_post_metadata(folder)
    assert updated[0]["status"] == "posted"
    assert updated[0]["yt_id"] == "YT_EXISTING"
    assert updated[0]["tt_id"] == "TT456"
