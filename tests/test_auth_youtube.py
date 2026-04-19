# tests/test_auth_youtube.py
import pickle
import sys
import types
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import auth_youtube


def test_check_existing_token_missing(tmp_path):
    token_path = tmp_path / "token.pickle"
    assert auth_youtube.check_existing_token(token_path) is False


def test_check_existing_token_invalid(tmp_path):
    token_path = tmp_path / "token.pickle"
    creds = types.SimpleNamespace(valid=False)
    with open(token_path, "wb") as f:
        pickle.dump(creds, f)
    assert auth_youtube.check_existing_token(token_path) is False


def test_check_existing_token_valid(tmp_path):
    token_path = tmp_path / "token.pickle"
    creds = types.SimpleNamespace(valid=True)
    with open(token_path, "wb") as f:
        pickle.dump(creds, f)
    assert auth_youtube.check_existing_token(token_path) is True


def test_parse_args_defaults():
    args = auth_youtube.parse_args([])
    assert args.secrets == Path("./secrets/client_secrets.json")
    assert args.token_out == Path("./secrets/token.pickle")


def test_parse_args_custom():
    args = auth_youtube.parse_args([
        "--secrets", "/tmp/secrets.json",
        "--token-out", "/tmp/token.pickle",
    ])
    assert args.secrets == Path("/tmp/secrets.json")
    assert args.token_out == Path("/tmp/token.pickle")


def test_run_auth_skips_if_valid(tmp_path, capsys):
    token_path = tmp_path / "token.pickle"
    creds = types.SimpleNamespace(valid=True)
    with open(token_path, "wb") as f:
        pickle.dump(creds, f)

    auth_youtube.run_auth(
        secrets_path=tmp_path / "client_secrets.json",
        token_out=token_path,
    )

    captured = capsys.readouterr()
    assert "既存トークンは有効です" in captured.out


def test_run_auth_writes_token(tmp_path, capsys):
    secrets_path = tmp_path / "client_secrets.json"
    secrets_path.write_text("{}")
    token_path = tmp_path / "token.pickle"

    mock_creds = types.SimpleNamespace(id="dummy")
    mock_flow = MagicMock()
    mock_flow.run_local_server.return_value = mock_creds

    with patch("auth_youtube.InstalledAppFlow") as MockFlow:
        MockFlow.from_client_secrets_file.return_value = mock_flow
        auth_youtube.run_auth(secrets_path=secrets_path, token_out=token_path)

    assert token_path.exists()
    with open(token_path, "rb") as f:
        saved = pickle.load(f)
    assert saved == mock_creds

    captured = capsys.readouterr()
    assert str(token_path) in captured.out
