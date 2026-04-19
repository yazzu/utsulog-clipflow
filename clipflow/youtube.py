import os
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PATHS = {
    "jp": Path("/secrets/token_jp.pickle"),
    "en": Path("/secrets/token_en.pickle"),
}


def _get_credentials(lang: str):
    token_path = TOKEN_PATHS[lang]
    creds = None
    if token_path.exists():
        with open(token_path, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.environ["YOUTUBE_CLIENT_SECRETS_FILE"], SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(token_path, "wb") as f:
            pickle.dump(creds, f)
    return creds


def upload(file_path: Path, record: dict, lang: str) -> str:
    creds = _get_credentials(lang)
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": record["title"],
            "description": record["description"],
            "tags": record["tags"],
            "categoryId": record["categoryId"],
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": record["forKids"],
        },
    }

    media = MediaFileUpload(str(file_path), chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    return response["id"]
