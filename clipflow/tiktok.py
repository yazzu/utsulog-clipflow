import os
from pathlib import Path

import requests

_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"


def upload(file_path: Path, record: dict) -> str:
    access_token = os.environ["TIKTOK_ACCESS_TOKEN"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    file_size = file_path.stat().st_size
    payload = {
        "post_info": {
            "title": record["title"],
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size,
            "total_chunk_count": 1,
        },
    }

    resp = requests.post(_INIT_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()["data"]
    publish_id = data["publish_id"]
    upload_url = data["upload_url"]

    upload_headers = {
        "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
        "Content-Type": "video/mp4",
    }
    with open(file_path, "rb") as f:
        upload_resp = requests.put(upload_url, data=f, headers=upload_headers, timeout=120)
    upload_resp.raise_for_status()

    return publish_id
