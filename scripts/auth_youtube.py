# scripts/auth_youtube.py
import pickle
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def check_existing_token(token_path: Path) -> bool:
    if not token_path.exists():
        return False
    with open(token_path, "rb") as f:
        creds = pickle.load(f)
    return bool(creds and creds.valid)
