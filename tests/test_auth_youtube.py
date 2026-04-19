# tests/test_auth_youtube.py
import pickle
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import auth_youtube


def test_check_existing_token_missing(tmp_path):
    token_path = tmp_path / "token.pickle"
    assert auth_youtube.check_existing_token(token_path) is False


def test_check_existing_token_invalid(tmp_path):
    token_path = tmp_path / "token.pickle"
    creds = MagicMock()
    creds.valid = False
    creds.expired = False
    with open(token_path, "wb") as f:
        pickle.dump(creds, f)
    assert auth_youtube.check_existing_token(token_path) is False


def test_check_existing_token_valid(tmp_path):
    token_path = tmp_path / "token.pickle"
    creds = MagicMock()
    creds.valid = True
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
