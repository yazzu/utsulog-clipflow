import os
import shutil
from pathlib import Path

import boto3


def backup_file(file_path: Path, folder_name: str) -> None:
    date_part = folder_name.split("_")[0]  # "20260412"
    yyyy = date_part[:4]
    mm = date_part[4:6]
    prefix = os.environ["S3_PREFIX"]
    key = f"{prefix}/{yyyy}/{mm}/{folder_name}/{file_path.name}"

    s3 = boto3.client("s3")
    s3.upload_file(str(file_path), os.environ["S3_BUCKET"], key)


def delete_file(file_path: Path) -> None:
    file_path.unlink()


def cleanup_folder_if_empty(folder: Path) -> None:
    if not list(folder.glob("*.mp4")):
        shutil.rmtree(folder)
