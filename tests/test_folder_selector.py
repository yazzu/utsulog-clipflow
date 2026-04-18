import json
import pytest
from pathlib import Path
from clipflow.folder_selector import get_oldest_folder


def test_get_oldest_folder_returns_oldest(tmp_path):
    older = tmp_path / "20260410_1200_abc123"
    newer = tmp_path / "20260412_2233_3hqPAjxCLDs"
    older.mkdir()
    newer.mkdir()
    result = get_oldest_folder(str(tmp_path))
    assert result == older


def test_get_oldest_folder_single_folder(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    result = get_oldest_folder(str(tmp_path))
    assert result == folder


def test_get_oldest_folder_empty_dir(tmp_path):
    result = get_oldest_folder(str(tmp_path))
    assert result is None


def test_get_oldest_folder_nonexistent_dir():
    result = get_oldest_folder("/nonexistent/path/that/does/not/exist")
    assert result is None
