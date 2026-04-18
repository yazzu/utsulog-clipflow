import os
import pytest
import boto3
from moto import mock_aws
from pathlib import Path
from clipflow.storage import backup_file, delete_file, cleanup_folder_if_empty

BUCKET = "test-bucket"
REGION = "ap-northeast-1"


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)
    monkeypatch.setenv("S3_BUCKET", BUCKET)
    monkeypatch.setenv("S3_PREFIX", "backup")


@pytest.fixture
def s3_bucket():
    with mock_aws():
        s3 = boto3.client("s3", region_name=REGION)
        s3.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
        yield s3


def test_backup_file_uploads_to_correct_key(s3_bucket, tmp_path):
    file_path = tmp_path / "highlight_001_ja.mp4"
    file_path.write_bytes(b"fake video")
    backup_file(file_path, "20260412_2233_3hqPAjxCLDs")
    obj = s3_bucket.get_object(
        Bucket=BUCKET,
        Key="backup/2026/04/20260412_2233_3hqPAjxCLDs/highlight_001_ja.mp4",
    )
    assert obj["Body"].read() == b"fake video"


def test_delete_file_removes_local_file(tmp_path):
    file_path = tmp_path / "highlight_001_ja.mp4"
    file_path.write_bytes(b"data")
    delete_file(file_path)
    assert not file_path.exists()


def test_cleanup_folder_if_empty_removes_folder(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    (folder / "post_metadata.ndjson").write_text("{}\n")  # 動画ファイルなし
    cleanup_folder_if_empty(folder)
    assert not folder.exists()


def test_cleanup_folder_if_empty_keeps_folder_with_mp4(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    (folder / "highlight_002_ja.mp4").write_bytes(b"video")
    cleanup_folder_if_empty(folder)
    assert folder.exists()
