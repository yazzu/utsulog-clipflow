# scripts/auth_youtube.py
import argparse
import pickle
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def check_existing_token(token_path: Path) -> bool:
    if not token_path.exists():
        return False
    with open(token_path, "rb") as f:
        creds = pickle.load(f)
    return bool(creds and creds.valid)


def run_auth(secrets_path: Path, token_out: Path) -> None:
    if check_existing_token(token_out):
        print("既存トークンは有効です。再認証する場合は削除してください:")
        print(f"  rm {token_out}")
        return

    flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
    creds = flow.run_local_server(port=0)

    token_out.parent.mkdir(parents=True, exist_ok=True)
    with open(token_out, "wb") as f:
        pickle.dump(creds, f)

    print(f"token.pickle を保存しました: {token_out}")


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
