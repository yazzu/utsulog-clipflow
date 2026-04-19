# scripts/auth_youtube.py
import argparse
import pickle
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def check_existing_token(token_path: Path) -> bool:
    if not token_path.exists():
        return False
    with open(token_path, "rb") as f:
        creds = pickle.load(f)
    return bool(creds and creds.valid)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YouTube OAuth 初回認証ツール")
    parser.add_argument(
        "--secrets",
        type=Path,
        default=Path("./secrets/client_secrets.json"),
        help="client_secrets.json のパス",
    )
    parser.add_argument(
        "--token-out",
        type=Path,
        default=Path("./secrets/token.pickle"),
        help="token.pickle の出力先",
    )
    return parser.parse_args(argv)
