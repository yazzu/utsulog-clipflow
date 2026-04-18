# ClipFlow コア処理フロー 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `pending` ディレクトリの動画を1本ずつ YouTube / TikTok に投稿し、成功後 S3 バックアップする Python スクリプト群を Docker 環境で動作させる。

**Architecture:** `main.py` が処理フローを統括し、`folder_selector` / `metadata` / `youtube` / `tiktok` / `storage` の5モジュールが各責務を担う。TDD で実装し、外部 API は `unittest.mock` / `moto` でモックする。

**Tech Stack:** Python 3.12, google-api-python-client, requests, boto3, python-dotenv, moto[s3], pytest, Docker

---

## ファイルマップ

| パス | 役割 |
|---|---|
| `clipflow/__init__.py` | パッケージ宣言 |
| `clipflow/folder_selector.py` | pending フォルダ・次投稿ファイルの選択 |
| `clipflow/metadata.py` | post_metadata.ndjson / ab_metadata.ndjson の読み書き |
| `clipflow/youtube.py` | YouTube Data API v3 投稿 |
| `clipflow/tiktok.py` | TikTok API 投稿 |
| `clipflow/storage.py` | S3 バックアップ・ローカル削除 |
| `clipflow/main.py` | エントリポイント（--lang jp/en） |
| `tests/test_folder_selector.py` | folder_selector ユニットテスト |
| `tests/test_metadata.py` | metadata ユニットテスト |
| `tests/test_storage.py` | storage ユニットテスト（moto） |
| `tests/test_main.py` | main 統合テスト（各モジュールをモック） |
| `Dockerfile` | python:3.12-slim ベース |
| `docker-compose.yml` | ボリュームマウント・env_file 設定 |
| `requirements.txt` | 依存ライブラリ |
| `.env.example` | 環境変数サンプル |

**言語マッピング注意点:**
- `post_metadata.ndjson` の `lang` フィールド: `"jp"` / `"en"`
- `ab_metadata.ndjson` の `language` フィールド: `"ja"` / `"en"`
- `--lang jp` → `ab_metadata` 参照時は `"ja"` に変換する

---

## Task 1: プロジェクトスキャフォールド

**Files:**
- Create: `clipflow/__init__.py`
- Create: `requirements.txt`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: `clipflow/__init__.py` を作成する**

```python
```

（空ファイル）

- [ ] **Step 2: `requirements.txt` を作成する**

```
google-api-python-client==2.151.0
google-auth-oauthlib==1.2.1
google-auth-httplib2==0.2.0
requests==2.32.3
boto3==1.35.99
python-dotenv==1.0.1
moto[s3]==5.0.27
pytest==8.3.5
```

- [ ] **Step 3: `Dockerfile` を作成する**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY clipflow/ clipflow/
```

- [ ] **Step 4: `docker-compose.yml` を作成する**

```yaml
services:
  clipflow:
    build: .
    env_file: .env
    volumes:
      - ${PENDING_DIR}:/data/pending
      - ./secrets:/secrets:ro
```

- [ ] **Step 5: `.env.example` を作成する**

```env
PENDING_DIR=/home/yazzu709/share/utsulog-clip/pending
S3_BUCKET=utsulog-clip-bucket
S3_PREFIX=backup
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_DEFAULT_REGION=ap-northeast-1
YOUTUBE_CLIENT_SECRETS_FILE=/secrets/client_secrets.json
TIKTOK_ACCESS_TOKEN=your_token_here
```

- [ ] **Step 6: Docker ビルドが通ることを確認する**

```bash
docker compose build
```

期待出力: `Successfully built ...`（エラーなし）

- [ ] **Step 7: コミットする**

```bash
git add clipflow/__init__.py requirements.txt Dockerfile docker-compose.yml .env.example
git commit -m "chore: add project scaffold (Dockerfile, requirements, docker-compose)"
```

---

## Task 2: `folder_selector.py` — `get_oldest_folder`

**Files:**
- Create: `clipflow/folder_selector.py`
- Create: `tests/test_folder_selector.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_folder_selector.py` を作成する:

```python
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
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_folder_selector.py -v
```

期待出力: `ERROR` または `ImportError: cannot import name 'get_oldest_folder'`

- [ ] **Step 3: 最小実装を書く**

`clipflow/folder_selector.py` を作成する:

```python
import json
from pathlib import Path


def get_oldest_folder(pending_dir: str) -> Path | None:
    base = Path(pending_dir)
    if not base.exists():
        return None
    folders = sorted(
        [f for f in base.iterdir() if f.is_dir()],
        key=lambda f: f.name,
    )
    return folders[0] if folders else None
```

- [ ] **Step 4: テストを実行して通ることを確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_folder_selector.py::test_get_oldest_folder_returns_oldest tests/test_folder_selector.py::test_get_oldest_folder_single_folder tests/test_folder_selector.py::test_get_oldest_folder_empty_dir tests/test_folder_selector.py::test_get_oldest_folder_nonexistent_dir -v
```

期待出力: `4 passed`

- [ ] **Step 5: コミットする**

```bash
git add clipflow/folder_selector.py tests/test_folder_selector.py
git commit -m "feat: add get_oldest_folder to folder_selector"
```

---

## Task 3: `folder_selector.py` — `get_next_file`

**Files:**
- Modify: `clipflow/folder_selector.py`
- Modify: `tests/test_folder_selector.py`

- [ ] **Step 1: 失敗するテストを追加する**

`tests/test_folder_selector.py` の末尾に追記する:

```python
import json


def _write_post_metadata(folder: Path, records: list) -> None:
    with open(folder / "post_metadata.ndjson", "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def test_get_next_file_returns_pending_by_highlight_no(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    _write_post_metadata(folder, [
        {"file": "highlight_002_ja.mp4", "lang": "jp", "highlight_no": 2, "status": "pending", "yt_id": "", "tt_id": ""},
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    result = get_next_file(folder, "jp")
    assert result["file"] == "highlight_001_ja.mp4"


def test_get_next_file_filters_by_lang(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    _write_post_metadata(folder, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "status": "pending", "yt_id": "", "tt_id": ""},
        {"file": "highlight_001_en.mp4", "lang": "en", "highlight_no": 1, "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    result = get_next_file(folder, "en")
    assert result["file"] == "highlight_001_en.mp4"


def test_get_next_file_prefers_pending_over_partial(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    _write_post_metadata(folder, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "status": "partial", "yt_id": "abc", "tt_id": ""},
        {"file": "highlight_002_ja.mp4", "lang": "jp", "highlight_no": 2, "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    result = get_next_file(folder, "jp")
    assert result["file"] == "highlight_002_ja.mp4"


def test_get_next_file_returns_partial_when_no_pending(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    _write_post_metadata(folder, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "status": "posted", "yt_id": "x", "tt_id": "y"},
        {"file": "highlight_002_ja.mp4", "lang": "jp", "highlight_no": 2, "status": "partial", "yt_id": "abc", "tt_id": ""},
    ])
    result = get_next_file(folder, "jp")
    assert result["file"] == "highlight_002_ja.mp4"


def test_get_next_file_returns_none_when_all_posted(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    _write_post_metadata(folder, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "status": "posted", "yt_id": "x", "tt_id": "y"},
    ])
    result = get_next_file(folder, "jp")
    assert result is None


def test_get_next_file_returns_none_for_unknown_lang(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    _write_post_metadata(folder, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    result = get_next_file(folder, "en")
    assert result is None
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_folder_selector.py -v -k "get_next_file"
```

期待出力: `ImportError: cannot import name 'get_next_file'`

- [ ] **Step 3: `get_next_file` を実装する**

`clipflow/folder_selector.py` に追記する（既存の `get_oldest_folder` は変更しない）:

```python
def get_next_file(folder: Path, lang: str) -> dict | None:
    metadata_path = folder / "post_metadata.ndjson"
    records = []
    with open(metadata_path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    candidates = [
        r for r in records
        if r["lang"] == lang and r["status"] in ("pending", "partial")
    ]
    if not candidates:
        return None

    candidates.sort(key=lambda r: (r["highlight_no"], 0 if r["status"] == "pending" else 1))
    return candidates[0]
```

`folder_selector.py` 先頭の import に `json` を追加する:

```python
import json
from pathlib import Path
```

- [ ] **Step 4: テストを実行して通ることを確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_folder_selector.py -v
```

期待出力: `10 passed`（Task 2 の4件 + 今回の6件）

- [ ] **Step 5: コミットする**

```bash
git add clipflow/folder_selector.py tests/test_folder_selector.py
git commit -m "feat: add get_next_file to folder_selector"
```

---

## Task 4: `metadata.py` — `read_post_metadata` / `write_post_metadata`

**Files:**
- Create: `clipflow/metadata.py`
- Create: `tests/test_metadata.py`

テストには `tests/fixtures/20260412_2233_3hqPAjxCLDs/post_metadata.ndjson` を使用する。

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_metadata.py` を作成する:

```python
import json
import pytest
from pathlib import Path
from clipflow.metadata import read_post_metadata, write_post_metadata

FIXTURE_FOLDER = Path("tests/fixtures/20260412_2233_3hqPAjxCLDs")


def test_read_post_metadata_returns_all_records():
    records = read_post_metadata(FIXTURE_FOLDER)
    assert len(records) == 6


def test_read_post_metadata_fields():
    records = read_post_metadata(FIXTURE_FOLDER)
    first = records[0]
    assert first["file"] == "highlight_001_ja.mp4"
    assert first["lang"] == "jp"
    assert first["highlight_no"] == 1
    assert first["status"] == "pending"


def test_write_post_metadata_roundtrip(tmp_path):
    original = read_post_metadata(FIXTURE_FOLDER)
    write_post_metadata(tmp_path, original)

    written = read_post_metadata(tmp_path)
    assert len(written) == len(original)
    assert written[0]["file"] == original[0]["file"]
    assert written[0]["title"] == original[0]["title"]


def test_write_post_metadata_preserves_japanese(tmp_path):
    records = [{"file": "a.mp4", "title": "日本語テスト", "lang": "jp"}]
    write_post_metadata(tmp_path, records)
    result = read_post_metadata(tmp_path)
    assert result[0]["title"] == "日本語テスト"
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_metadata.py -v
```

期待出力: `ImportError: cannot import name 'read_post_metadata'`

- [ ] **Step 3: `read_post_metadata` / `write_post_metadata` を実装する**

`clipflow/metadata.py` を作成する:

```python
import json
from pathlib import Path


def read_post_metadata(folder: Path) -> list:
    path = folder / "post_metadata.ndjson"
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_post_metadata(folder: Path, records: list) -> None:
    path = folder / "post_metadata.ndjson"
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

- [ ] **Step 4: テストを実行して通ることを確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_metadata.py -v
```

期待出力: `4 passed`

- [ ] **Step 5: コミットする**

```bash
git add clipflow/metadata.py tests/test_metadata.py
git commit -m "feat: add read/write_post_metadata to metadata"
```

---

## Task 5: `metadata.py` — `update_post_metadata`

**Files:**
- Modify: `clipflow/metadata.py`
- Modify: `tests/test_metadata.py`

- [ ] **Step 1: 失敗するテストを追加する**

`tests/test_metadata.py` に追記する:

```python
from clipflow.metadata import update_post_metadata


def _make_folder(tmp_path: Path, records: list) -> Path:
    write_post_metadata(tmp_path, records)
    return tmp_path


def test_update_post_metadata_both_success(tmp_path):
    _make_folder(tmp_path, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1,
         "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    update_post_metadata(tmp_path, "highlight_001_ja.mp4", yt_id="YT123", tt_id="TT456")
    result = read_post_metadata(tmp_path)
    assert result[0]["status"] == "posted"
    assert result[0]["yt_id"] == "YT123"
    assert result[0]["tt_id"] == "TT456"


def test_update_post_metadata_yt_only(tmp_path):
    _make_folder(tmp_path, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1,
         "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    update_post_metadata(tmp_path, "highlight_001_ja.mp4", yt_id="YT123", tt_id=None)
    result = read_post_metadata(tmp_path)
    assert result[0]["status"] == "partial"
    assert result[0]["yt_id"] == "YT123"
    assert result[0]["tt_id"] == ""


def test_update_post_metadata_tt_only(tmp_path):
    _make_folder(tmp_path, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1,
         "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    update_post_metadata(tmp_path, "highlight_001_ja.mp4", yt_id=None, tt_id="TT456")
    result = read_post_metadata(tmp_path)
    assert result[0]["status"] == "partial"
    assert result[0]["yt_id"] == ""
    assert result[0]["tt_id"] == "TT456"


def test_update_post_metadata_both_fail(tmp_path):
    _make_folder(tmp_path, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1,
         "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    update_post_metadata(tmp_path, "highlight_001_ja.mp4", yt_id=None, tt_id=None)
    result = read_post_metadata(tmp_path)
    assert result[0]["status"] == "pending"


def test_update_post_metadata_partial_completes(tmp_path):
    """既に yt_id がある partial レコードに tt_id を追加すると posted になる"""
    _make_folder(tmp_path, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1,
         "status": "partial", "yt_id": "YT123", "tt_id": ""},
    ])
    update_post_metadata(tmp_path, "highlight_001_ja.mp4", yt_id=None, tt_id="TT456")
    result = read_post_metadata(tmp_path)
    assert result[0]["status"] == "posted"
    assert result[0]["yt_id"] == "YT123"
    assert result[0]["tt_id"] == "TT456"


def test_update_post_metadata_only_updates_target_file(tmp_path):
    _make_folder(tmp_path, [
        {"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1,
         "status": "pending", "yt_id": "", "tt_id": ""},
        {"file": "highlight_002_ja.mp4", "lang": "jp", "highlight_no": 2,
         "status": "pending", "yt_id": "", "tt_id": ""},
    ])
    update_post_metadata(tmp_path, "highlight_001_ja.mp4", yt_id="YT123", tt_id="TT456")
    result = read_post_metadata(tmp_path)
    assert result[1]["status"] == "pending"
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_metadata.py -v -k "update_post"
```

期待出力: `ImportError: cannot import name 'update_post_metadata'`

- [ ] **Step 3: `update_post_metadata` を実装する**

`clipflow/metadata.py` に追記する（既存の関数は変更しない）:

```python
def update_post_metadata(
    folder: Path, file: str, yt_id: str | None, tt_id: str | None
) -> None:
    records = read_post_metadata(folder)
    for record in records:
        if record["file"] != file:
            continue
        if yt_id:
            record["yt_id"] = yt_id
        if tt_id:
            record["tt_id"] = tt_id
        has_yt = bool(record.get("yt_id"))
        has_tt = bool(record.get("tt_id"))
        if has_yt and has_tt:
            record["status"] = "posted"
        elif has_yt or has_tt:
            record["status"] = "partial"
        break
    write_post_metadata(folder, records)
```

- [ ] **Step 4: テストを実行して通ることを確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_metadata.py -v
```

期待出力: `10 passed`

- [ ] **Step 5: コミットする**

```bash
git add clipflow/metadata.py tests/test_metadata.py
git commit -m "feat: add update_post_metadata to metadata"
```

---

## Task 6: `metadata.py` — `update_ab_metadata`

**Files:**
- Modify: `clipflow/metadata.py`
- Modify: `tests/test_metadata.py`

**注意:** `ab_metadata.ndjson` の `language` フィールドは `"ja"` / `"en"`。`lang` 引数 `"jp"` は内部で `"ja"` に変換する。

- [ ] **Step 1: 失敗するテストを追加する**

`tests/test_metadata.py` に追記する:

```python
from clipflow.metadata import update_ab_metadata


def _write_ab_metadata(folder: Path, records: list) -> None:
    path = folder / "ab_metadata.ndjson"
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _read_ab_metadata(folder: Path) -> list:
    path = folder / "ab_metadata.ndjson"
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def test_update_ab_metadata_adds_yt_id(tmp_path):
    _write_ab_metadata(tmp_path, [
        {"highlight_id": "highlight_001", "language": "ja", "video_id": None, "yt_id": None, "tt_id": None},
    ])
    update_ab_metadata(tmp_path, "highlight_001", "jp", yt_id="YT123", tt_id=None)
    result = _read_ab_metadata(tmp_path)
    assert result[0]["yt_id"] == "YT123"
    assert result[0]["tt_id"] is None


def test_update_ab_metadata_adds_tt_id(tmp_path):
    _write_ab_metadata(tmp_path, [
        {"highlight_id": "highlight_001", "language": "ja", "video_id": None, "yt_id": None, "tt_id": None},
    ])
    update_ab_metadata(tmp_path, "highlight_001", "jp", yt_id=None, tt_id="TT456")
    result = _read_ab_metadata(tmp_path)
    assert result[0]["tt_id"] == "TT456"


def test_update_ab_metadata_maps_jp_to_ja(tmp_path):
    _write_ab_metadata(tmp_path, [
        {"highlight_id": "highlight_001", "language": "ja", "video_id": None, "yt_id": None, "tt_id": None},
        {"highlight_id": "highlight_001", "language": "en", "video_id": None, "yt_id": None, "tt_id": None},
    ])
    update_ab_metadata(tmp_path, "highlight_001", "jp", yt_id="YT123", tt_id=None)
    result = _read_ab_metadata(tmp_path)
    assert result[0]["yt_id"] == "YT123"   # language="ja" のレコードが更新される
    assert result[1]["yt_id"] is None       # language="en" は変更なし


def test_update_ab_metadata_en_lang(tmp_path):
    _write_ab_metadata(tmp_path, [
        {"highlight_id": "highlight_001", "language": "en", "video_id": None, "yt_id": None, "tt_id": None},
    ])
    update_ab_metadata(tmp_path, "highlight_001", "en", yt_id="YT999", tt_id="TT888")
    result = _read_ab_metadata(tmp_path)
    assert result[0]["yt_id"] == "YT999"
    assert result[0]["tt_id"] == "TT888"


def test_update_ab_metadata_does_not_overwrite_existing_video_id(tmp_path):
    _write_ab_metadata(tmp_path, [
        {"highlight_id": "highlight_001", "language": "ja", "video_id": "ORIGINAL", "yt_id": None, "tt_id": None},
    ])
    update_ab_metadata(tmp_path, "highlight_001", "jp", yt_id="YT123", tt_id=None)
    result = _read_ab_metadata(tmp_path)
    assert result[0]["video_id"] == "ORIGINAL"  # 既存フィールドは変更しない
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_metadata.py -v -k "ab_metadata"
```

期待出力: `ImportError: cannot import name 'update_ab_metadata'`

- [ ] **Step 3: `update_ab_metadata` を実装する**

`clipflow/metadata.py` に追記する:

```python
_LANG_MAP = {"jp": "ja"}


def update_ab_metadata(
    folder: Path,
    highlight_id: str,
    lang: str,
    yt_id: str | None,
    tt_id: str | None,
) -> None:
    ab_lang = _LANG_MAP.get(lang, lang)
    path = folder / "ab_metadata.ndjson"
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    for record in records:
        if record["highlight_id"] == highlight_id and record["language"] == ab_lang:
            if yt_id:
                record["yt_id"] = yt_id
            if tt_id:
                record["tt_id"] = tt_id
            break

    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

- [ ] **Step 4: テストを実行して通ることを確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_metadata.py -v
```

期待出力: `15 passed`

- [ ] **Step 5: コミットする**

```bash
git add clipflow/metadata.py tests/test_metadata.py
git commit -m "feat: add update_ab_metadata to metadata"
```

---

## Task 7: `storage.py`

**Files:**
- Create: `clipflow/storage.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_storage.py` を作成する:

```python
import os
import pytest
import boto3
from moto import mock_aws
from pathlib import Path
from clipflow.storage import backup_file, delete_file, cleanup_folder_if_empty

BUCKET = "test-bucket"
REGION = "ap-northeast-1"


@pytest.fixture(autouse=True)
def aws_env(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", REGION)
    monkeypatch.setenv("S3_BUCKET", BUCKET)
    monkeypatch.setenv("S3_PREFIX", "backup")


@pytest.fixture
def s3_bucket():
    with mock_aws():
        s3 = boto3.client("s3", region_name=REGION)
        s3.create_bucket(
            Bucket=BUCKET,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
        yield s3


def test_backup_file_uploads_to_correct_key(s3_bucket, tmp_path):
    file_path = tmp_path / "highlight_001_ja.mp4"
    file_path.write_bytes(b"fake video")
    backup_file(file_path, "20260412_2233_3hqPAjxCLDs")
    obj = s3_bucket.get_object(
        Bucket=BUCKET,
        Key="backup/2026/04/20260412_2233_3hqPAjxCLDs/highlight_001_ja.mp4",
    )
    assert obj["Body"].read() == b"fake video"


def test_delete_file_removes_local_file(tmp_path):
    file_path = tmp_path / "highlight_001_ja.mp4"
    file_path.write_bytes(b"data")
    delete_file(file_path)
    assert not file_path.exists()


def test_cleanup_folder_if_empty_removes_folder(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    (folder / "post_metadata.ndjson").write_text("{}\n")  # 動画ファイルなし
    cleanup_folder_if_empty(folder)
    assert not folder.exists()


def test_cleanup_folder_if_empty_keeps_folder_with_mp4(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    (folder / "highlight_002_ja.mp4").write_bytes(b"video")
    cleanup_folder_if_empty(folder)
    assert folder.exists()
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_storage.py -v
```

期待出力: `ImportError: cannot import name 'backup_file'`

- [ ] **Step 3: `storage.py` を実装する**

`clipflow/storage.py` を作成する:

```python
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
```

- [ ] **Step 4: テストを実行して通ることを確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_storage.py -v
```

期待出力: `4 passed`

- [ ] **Step 5: コミットする**

```bash
git add clipflow/storage.py tests/test_storage.py
git commit -m "feat: add storage module (S3 backup, local delete, folder cleanup)"
```

---

## Task 8: `youtube.py`

**Files:**
- Create: `clipflow/youtube.py`

`youtube.py` は実 API への呼び出しを持つため、ユニットテストは `main.py` の統合テスト（Task 10）でモックして検証する。

- [ ] **Step 1: `youtube.py` を実装する**

`clipflow/youtube.py` を作成する:

```python
import os
import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PATH = Path("/secrets/token.pickle")


def _get_credentials():
    creds = None
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.environ["YOUTUBE_CLIENT_SECRETS_FILE"], SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as f:
            pickle.dump(creds, f)
    return creds


def upload(file_path: Path, record: dict) -> str:
    creds = _get_credentials()
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
```

- [ ] **Step 2: import が通ることを確認する**

```bash
docker compose run --rm clipflow python -c "from clipflow.youtube import upload; print('OK')"
```

期待出力: `OK`

- [ ] **Step 3: コミットする**

```bash
git add clipflow/youtube.py
git commit -m "feat: add youtube upload module"
```

---

## Task 9: `tiktok.py`

**Files:**
- Create: `clipflow/tiktok.py`

`tiktok.py` も実 API 呼び出しのため、ユニットテストは Task 10 の統合テストでモックして検証する。

- [ ] **Step 1: `tiktok.py` を実装する**

`clipflow/tiktok.py` を作成する:

```python
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

    with open(file_path, "rb") as f:
        video_data = f.read()

    upload_headers = {
        "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
        "Content-Type": "video/mp4",
    }
    upload_resp = requests.put(upload_url, data=video_data, headers=upload_headers, timeout=120)
    upload_resp.raise_for_status()

    return publish_id
```

- [ ] **Step 2: import が通ることを確認する**

```bash
docker compose run --rm clipflow python -c "from clipflow.tiktok import upload; print('OK')"
```

期待出力: `OK`

- [ ] **Step 3: コミットする**

```bash
git add clipflow/tiktok.py
git commit -m "feat: add tiktok upload module"
```

---

## Task 10: `main.py` — 統合テスト + 実装

**Files:**
- Create: `clipflow/main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_main.py` を作成する:

```python
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from clipflow.main import run


@pytest.fixture
def pending_folder(tmp_path):
    folder = tmp_path / "20260412_2233_3hqPAjxCLDs"
    folder.mkdir()
    records = [
        {
            "file": "highlight_001_ja.mp4",
            "lang": "jp",
            "highlight_no": 1,
            "title": "テスト",
            "description": "説明",
            "tags": ["tag1"],
            "categoryId": "20",
            "forKids": False,
            "status": "pending",
            "yt_id": "",
            "tt_id": "",
        }
    ]
    with open(folder / "post_metadata.ndjson", "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(folder / "ab_metadata.ndjson", "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "highlight_id": "highlight_001",
            "language": "ja",
            "video_id": None,
            "yt_id": None,
            "tt_id": None,
        }, ensure_ascii=False) + "\n")
    video = folder / "highlight_001_ja.mp4"
    video.write_bytes(b"fake")
    return tmp_path, folder


def test_run_both_success_marks_posted_and_backups(pending_folder, monkeypatch):
    pending_dir, folder = pending_folder
    monkeypatch.setenv("PENDING_DIR", str(pending_dir))
    monkeypatch.setenv("S3_BUCKET", "test-bucket")
    monkeypatch.setenv("S3_PREFIX", "backup")

    with (
        patch("clipflow.main.youtube.upload", return_value="YT123") as mock_yt,
        patch("clipflow.main.tiktok.upload", return_value="TT456") as mock_tt,
        patch("clipflow.main.storage.backup_file") as mock_backup,
        patch("clipflow.main.storage.delete_file") as mock_delete,
        patch("clipflow.main.storage.cleanup_folder_if_empty") as mock_cleanup,
    ):
        run("jp")

    mock_yt.assert_called_once()
    mock_tt.assert_called_once()
    mock_backup.assert_called_once()
    mock_delete.assert_called_once()
    mock_cleanup.assert_called_once()

    from clipflow.metadata import read_post_metadata
    records = read_post_metadata(folder)
    assert records[0]["status"] == "posted"
    assert records[0]["yt_id"] == "YT123"
    assert records[0]["tt_id"] == "TT456"


def test_run_yt_fail_marks_partial_no_backup(pending_folder, monkeypatch):
    pending_dir, folder = pending_folder
    monkeypatch.setenv("PENDING_DIR", str(pending_dir))

    with (
        patch("clipflow.main.youtube.upload", side_effect=Exception("YT error")),
        patch("clipflow.main.tiktok.upload", return_value="TT456"),
        patch("clipflow.main.storage.backup_file") as mock_backup,
        patch("clipflow.main.storage.delete_file") as mock_delete,
        patch("clipflow.main.storage.cleanup_folder_if_empty") as mock_cleanup,
    ):
        run("jp")

    mock_backup.assert_not_called()
    mock_delete.assert_not_called()
    mock_cleanup.assert_not_called()

    from clipflow.metadata import read_post_metadata
    records = read_post_metadata(folder)
    assert records[0]["status"] == "partial"
    assert records[0]["yt_id"] == ""
    assert records[0]["tt_id"] == "TT456"


def test_run_both_fail_stays_pending(pending_folder, monkeypatch):
    pending_dir, folder = pending_folder
    monkeypatch.setenv("PENDING_DIR", str(pending_dir))

    with (
        patch("clipflow.main.youtube.upload", side_effect=Exception("YT error")),
        patch("clipflow.main.tiktok.upload", side_effect=Exception("TT error")),
        patch("clipflow.main.storage.backup_file") as mock_backup,
    ):
        run("jp")

    mock_backup.assert_not_called()

    from clipflow.metadata import read_post_metadata
    records = read_post_metadata(folder)
    assert records[0]["status"] == "pending"


def test_run_no_pending_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("PENDING_DIR", str(tmp_path))
    with patch("clipflow.main.youtube.upload") as mock_yt:
        run("jp")
    mock_yt.assert_not_called()


def test_run_partial_retries_missing_platform(pending_folder, monkeypatch):
    """partial レコードは欠けているプラットフォームのみ投稿する"""
    pending_dir, folder = pending_folder
    monkeypatch.setenv("PENDING_DIR", str(pending_dir))

    # yt_id が既にあり tt_id が空の partial レコードに更新
    from clipflow.metadata import read_post_metadata, write_post_metadata
    records = read_post_metadata(folder)
    records[0]["status"] = "partial"
    records[0]["yt_id"] = "YT_EXISTING"
    write_post_metadata(folder, records)

    with (
        patch("clipflow.main.youtube.upload") as mock_yt,
        patch("clipflow.main.tiktok.upload", return_value="TT456") as mock_tt,
        patch("clipflow.main.storage.backup_file"),
        patch("clipflow.main.storage.delete_file"),
        patch("clipflow.main.storage.cleanup_folder_if_empty"),
    ):
        run("jp")

    mock_yt.assert_not_called()  # yt_id が既にあるので呼ばない
    mock_tt.assert_called_once()

    updated = read_post_metadata(folder)
    assert updated[0]["status"] == "posted"
    assert updated[0]["yt_id"] == "YT_EXISTING"
    assert updated[0]["tt_id"] == "TT456"
```

- [ ] **Step 2: テストを実行して失敗を確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/test_main.py -v
```

期待出力: `ImportError: cannot import name 'run'`

- [ ] **Step 3: `main.py` を実装する**

`clipflow/main.py` を作成する:

```python
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
        metadata.update_ab_metadata(folder, highlight_id, lang, yt_id, tt_id)

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
```

- [ ] **Step 4: テストを実行して通ることを確認する**

```bash
docker compose run --rm clipflow python -m pytest tests/ -v
```

期待出力: `全テスト passed`（test_main 5件 + 累計）

- [ ] **Step 5: コミットする**

```bash
git add clipflow/main.py tests/test_main.py
git commit -m "feat: add main entrypoint with integration tests"
```

---

## Task 11: 全テストを Docker で実行して確認する

- [ ] **Step 1: 全テストスイートを実行する**

```bash
docker compose run --rm clipflow python -m pytest tests/ -v
```

期待出力: 全テスト PASSED、エラーなし

- [ ] **Step 2: systemd.timer 用コマンドを手動で確認する（--lang 引数）**

```bash
docker compose run --rm clipflow python clipflow/main.py --help
```

期待出力:
```
usage: main.py [-h] --lang {jp,en}
```

- [ ] **Step 3: 最終コミットする**

```bash
git add .
git commit -m "chore: verify all tests pass in Docker"
```
