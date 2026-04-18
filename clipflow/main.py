import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from clipflow import folder_selector, metadata, youtube, tiktok, storage

logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def run(lang: str) -> None:
    pending_dir = os.environ["PENDING_DIR"]

    folder = folder_selector.get_oldest_folder(pending_dir)
    if folder is None:
        logger.info("No pending folders found.")
        return

    record = folder_selector.get_next_file(folder, lang)
    if record is None:
        logger.info("No pending files in %s for lang=%s.", folder.name, lang)
        return

    file_path = folder / record["file"]
    logger.info("Processing %s", file_path)

    yt_id = record.get("yt_id") or None
    tt_id = record.get("tt_id") or None

    if not yt_id:
        try:
            yt_id = youtube.upload(file_path, record)
            logger.info("YouTube upload success: %s", yt_id)
        except Exception as e:
            logger.error("YouTube upload failed: %s", e)
            yt_id = None

    if not tt_id:
        try:
            tt_id = tiktok.upload(file_path, record)
            logger.info("TikTok upload success: %s", tt_id)
        except Exception as e:
            logger.error("TikTok upload failed: %s", e)
            tt_id = None

    metadata.update_post_metadata(folder, record["file"], yt_id, tt_id)

    if yt_id or tt_id:
        stem = Path(record["file"]).stem          # "highlight_001_ja"
        highlight_id = "_".join(stem.split("_")[:-1])  # "highlight_001"
        try:
            metadata.update_ab_metadata(folder, highlight_id, lang, yt_id, tt_id)
        except Exception as e:
            logger.warning("ab_metadata update failed: %s", e)

    if yt_id and tt_id:
        try:
            storage.backup_file(file_path, folder.name)
            storage.delete_file(file_path)
            storage.cleanup_folder_if_empty(folder)
            logger.info("Backup and cleanup done: %s", file_path.name)
        except Exception as e:
            logger.error("Storage operation failed: %s", e)
    else:
        logger.warning(
            "Partial or no success for %s (yt_id=%s, tt_id=%s)",
            record["file"], yt_id, tt_id,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="ClipFlow auto poster")
    parser.add_argument("--lang", required=True, choices=["jp", "en"])
    args = parser.parse_args()
    run(args.lang)


if __name__ == "__main__":
    main()
