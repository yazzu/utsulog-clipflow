# YouTube 初回認証 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ホスト上で `python scripts/auth_youtube.py` を実行するだけで `./secrets/token.pickle` を生成できるようにし、初回認証手順書も整備する。

**Architecture:** Docker コンテナ外（ホスト）で OAuth ブラウザ認証を行い、生成した `token.pickle` を `./secrets/` に配置する。コンテナ起動時は read-only マウントで読み込む既存設計を変更しない。スクリプトは `clipflow` パッケージに依存せず `google-auth-oauthlib` のみに依存する。

**Tech Stack:** Python 3.x, google-auth-oauthlib, pickle, argparse

---

### Task 1: `check_existing_token` のテストと実装

**Files:**
- Create: `scripts/auth_youtube.py`
- Create: `tests/test_auth_youtube.py`

- [ ] **Step 1: テストファイルを作成する**

```python
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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest tests/test_auth_youtube.py -v
```

期待結果: `ModuleNotFoundError: No module named 'auth_youtube'`

- [ ] **Step 3: `scripts/auth_youtube.py` のスケルトンを作成する**

```python
# scripts/auth_youtube.py
import argparse
import pickle
import sys
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def check_existing_token(token_path: Path) -> bool:
    if not token_path.exists():
        return False
    with open(token_path, "rb") as f:
        creds = pickle.load(f)
    return bool(creds and creds.valid)
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
pytest tests/test_auth_youtube.py -v
```

期待結果: `3 passed`

- [ ] **Step 5: コミットする**

```bash
git add scripts/auth_youtube.py tests/test_auth_youtube.py
git commit -m "feat: add check_existing_token with tests"
```

---

### Task 2: 引数パースのテストと実装

**Files:**
- Modify: `scripts/auth_youtube.py`
- Modify: `tests/test_auth_youtube.py`

- [ ] **Step 1: テストを追加する**

`tests/test_auth_youtube.py` に以下を追記する:

```python
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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest tests/test_auth_youtube.py::test_parse_args_defaults -v
```

期待結果: `FAIL` — `AttributeError: module 'auth_youtube' has no attribute 'parse_args'`

- [ ] **Step 3: `parse_args` を実装する**

`scripts/auth_youtube.py` の末尾に追加する:

```python
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
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
pytest tests/test_auth_youtube.py -v
```

期待結果: `5 passed`

- [ ] **Step 5: コミットする**

```bash
git add scripts/auth_youtube.py tests/test_auth_youtube.py
git commit -m "feat: add parse_args with tests"
```

---

### Task 3: `run_auth` のテストと実装（OAuth フロー本体）

**Files:**
- Modify: `scripts/auth_youtube.py`
- Modify: `tests/test_auth_youtube.py`

- [ ] **Step 1: テストを追加する**

`tests/test_auth_youtube.py` に以下を追記する:

```python
from unittest.mock import patch, MagicMock


def test_run_auth_skips_if_valid(tmp_path, capsys):
    token_path = tmp_path / "token.pickle"
    creds = MagicMock()
    creds.valid = True
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

    mock_creds = MagicMock()
    mock_flow = MagicMock()
    mock_flow.run_local_server.return_value = mock_creds

    with patch("auth_youtube.InstalledAppFlow") as MockFlow:
        MockFlow.from_client_secrets_file.return_value = mock_flow
        auth_youtube.run_auth(secrets_path=secrets_path, token_out=token_path)

    assert token_path.exists()
    with open(token_path, "rb") as f:
        saved = pickle.load(f)
    assert saved is mock_creds

    captured = capsys.readouterr()
    assert str(token_path) in captured.out
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest tests/test_auth_youtube.py::test_run_auth_skips_if_valid -v
```

期待結果: `FAIL` — `AttributeError: module 'auth_youtube' has no attribute 'run_auth'`

- [ ] **Step 3: `run_auth` を実装する**

`scripts/auth_youtube.py` の先頭 import に追加:

```python
from google_auth_oauthlib.flow import InstalledAppFlow
```

続けて関数を追加:

```python
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
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
pytest tests/test_auth_youtube.py -v
```

期待結果: `7 passed`

- [ ] **Step 5: コミットする**

```bash
git add scripts/auth_youtube.py tests/test_auth_youtube.py
git commit -m "feat: add run_auth with OAuth flow and tests"
```

---

### Task 4: `main` エントリポイントの追加

**Files:**
- Modify: `scripts/auth_youtube.py`

- [ ] **Step 1: `main` を実装する**

`scripts/auth_youtube.py` の末尾に追加する:

```python
def main() -> None:
    args = parse_args()
    run_auth(secrets_path=args.secrets, token_out=args.token_out)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: スクリプトが `--help` で動くことを確認する**

```bash
python scripts/auth_youtube.py --help
```

期待結果:
```
usage: auth_youtube.py [-h] [--secrets SECRETS] [--token-out TOKEN_OUT]

YouTube OAuth 初回認証ツール
...
```

- [ ] **Step 3: テストがすべて通ることを確認する**

```bash
pytest tests/test_auth_youtube.py -v
```

期待結果: `7 passed`

- [ ] **Step 4: コミットする**

```bash
git add scripts/auth_youtube.py
git commit -m "feat: add main entrypoint to auth_youtube"
```

---

### Task 5: 手順書 `docs/setup/youtube-auth.md` を作成する

**Files:**
- Create: `docs/setup/youtube-auth.md`

- [ ] **Step 1: `docs/setup/` ディレクトリを作成する**

```bash
mkdir -p docs/setup
```

- [ ] **Step 2: 手順書を作成する**

`docs/setup/youtube-auth.md` を以下の内容で作成する:

```markdown
# YouTube 初回認証手順

## 前提条件

- Python 3.x がホスト（Raspberry Pi）にインストール済み
- `google-auth-oauthlib` をインストール済み:

  ```bash
  pip install google-auth-oauthlib
  ```

---

## 1. Google Cloud Console の設定（初回のみ）

### 1-1. プロジェクトを作成・選択する

1. [Google Cloud Console](https://console.cloud.google.com/) を開く
2. 上部のプロジェクト選択から「新しいプロジェクト」を作成するか、既存プロジェクトを選択する

### 1-2. YouTube Data API v3 を有効化する

1. 左メニュー → 「APIとサービス」→「ライブラリ」
2. 検索バーに「YouTube Data API v3」と入力
3. 「有効にする」をクリック

### 1-3. OAuth 同意画面を設定する

1. 左メニュー → 「APIとサービス」→「OAuth 同意画面」
2. ユーザーの種類: 「外部」を選択 → 「作成」
3. アプリ名・サポートメールを入力して「保存して次へ」
4. スコープは変更せず「保存して次へ」
5. テストユーザーに自分の Google アカウントを追加 → 「保存して次へ」

> **注意:** 同意画面が「テスト」状態の場合、トークンの有効期限が7日間になります。  
> 長期運用する場合は「本番環境」へ公開申請するか、定期的に再認証してください。

### 1-4. OAuth クライアント ID を作成する

1. 左メニュー → 「APIとサービス」→「認証情報」
2. 「認証情報を作成」→「OAuth クライアント ID」
3. アプリケーションの種類: 「デスクトップアプリ」を選択
4. 名前を入力して「作成」
5. 「JSON をダウンロード」をクリック

### 1-5. `client_secrets.json` を配置する

ダウンロードした JSON ファイルを `./secrets/client_secrets.json` としてリポジトリルートに配置する:

```bash
mv ~/Downloads/client_secret_*.json ./secrets/client_secrets.json
```

> `./secrets/` は `.gitignore` で除外されているため、誤ってコミットされません。

---

## 2. 初回認証

```bash
python scripts/auth_youtube.py --secrets ./secrets/client_secrets.json
```

1. ブラウザが自動的に開き、Google アカウントの選択画面が表示される
2. テストユーザーとして追加したアカウントでログインする
3. 「このアプリは確認されていません」と表示される場合は「詳細」→「（アプリ名）に移動」をクリック
4. アクセスを許可する
5. ターミナルに「token.pickle を保存しました: ./secrets/token.pickle」と表示されれば完了

---

## 3. 動作確認

```bash
docker compose run --rm clipflow python -m clipflow.main --lang jp
```

YouTube への投稿が成功すれば認証は正常に完了しています。

---

## 4. トークン期限切れ時の再認証

```bash
rm ./secrets/token.pickle
python scripts/auth_youtube.py --secrets ./secrets/client_secrets.json
```

「2. 初回認証」と同じ手順でブラウザ認証を行い、新しいトークンを取得します。
```

- [ ] **Step 3: コミットする**

```bash
git add docs/setup/youtube-auth.md
git commit -m "docs: add YouTube OAuth setup guide"
```

---

### Task 6: `.gitignore` を確認・更新する

**Files:**
- Modify: `.gitignore`（存在する場合）

- [ ] **Step 1: `.gitignore` に `secrets/` が含まれているか確認する**

```bash
cat .gitignore
```

- [ ] **Step 2: 含まれていない場合は追加する**

`.gitignore` に以下を追加する（すでにある場合はスキップ）:

```
secrets/
```

- [ ] **Step 3: `secrets/` が追跡されていないことを確認する**

```bash
git status
```

期待結果: `secrets/` ディレクトリが `Untracked files` に表示されない（または表示されない）こと。

- [ ] **Step 4: 変更があればコミットする**

```bash
git add .gitignore
git commit -m "chore: ensure secrets/ is gitignored"
```

---

## 完了チェックリスト

- [ ] `pytest tests/test_auth_youtube.py -v` が全テスト通過
- [ ] `python scripts/auth_youtube.py --help` が正常に動く
- [ ] `docs/setup/youtube-auth.md` が存在する
- [ ] `./secrets/` が `.gitignore` に含まれている
