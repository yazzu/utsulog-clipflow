# YouTube 初回認証手順 設計書

**日付:** 2026-04-19  
**対象:** clipflow プロジェクトの YouTube OAuth 初回認証フロー

---

## 概要

Docker コンテナ内ではブラウザが起動しないため、YouTube OAuth トークンの初回取得はホスト上で行う必要がある。本設計では以下の2つの成果物を作成することで、再現可能な認証手順を確立する。

1. `scripts/auth_youtube.py` — ホスト上で実行する認証スクリプト
2. `docs/setup/youtube-auth.md` — Google Cloud Console の設定手順 + スクリプト実行手順書

---

## アーキテクチャ

```
ホスト上で実行
  │
  ├─ scripts/auth_youtube.py
  │     ├─ --secrets 引数で client_secrets.json のパスを受け取る
  │     ├─ --token-out 引数で token.pickle の出力先を指定
  │     ├─ InstalledAppFlow.run_local_server() でブラウザ認証
  │     └─ token.pickle を ./secrets/ に書き出す
  │
  └─ docker compose 実行時に ./secrets/token.pickle が読み込まれる
         (volume: ./secrets:/secrets:ro)
```

`docker-compose.yml` の volume は `:ro`（読み取り専用）のままで問題ない。書き込みはホスト側で行うためコンテナ側の権限変更は不要。

---

## スクリプト設計: `scripts/auth_youtube.py`

### インターフェース

| 引数 | デフォルト | 説明 |
|------|-----------|------|
| `--secrets` | `./secrets/client_secrets.json` | client_secrets.json のパス |
| `--token-out` | `./secrets/token.pickle` | token.pickle の出力先 |

### 依存関係

- `google-auth-oauthlib` のみ（`clipflow` パッケージ不要）
- ホスト上で `pip install google-auth-oauthlib` 一発で動く

### スコープ

`youtube.py` と同じ `https://www.googleapis.com/auth/youtube.upload` を使用。

### 動作

1. `--token-out` に有効な `token.pickle` が既に存在する場合 → 「既存トークンは有効です」と表示して終了（誤上書き防止）
2. 存在しないか無効な場合 → ブラウザ認証フローを開始
3. 認証成功後 → `token.pickle` を書き出し、保存先パスを表示して終了

---

## 手順書の構成: `docs/setup/youtube-auth.md`

### 1. 前提条件
- gcloud CLI セットアップ済み
- `pip install google-auth-oauthlib` でライブラリをインストール済み

### 2. Google Cloud Console の設定（初回のみ）
1. プロジェクト作成 or 選択
2. YouTube Data API v3 を有効化
3. OAuth 同意画面の設定（テスト用）
4. OAuth クライアント ID を作成（種別: デスクトップアプリ）
5. `client_secrets.json` をダウンロードして `./secrets/` に配置

### 3. 初回認証
```bash
python scripts/auth_youtube.py --secrets ./secrets/client_secrets.json
```
ブラウザが開くので Google アカウントでログイン → `./secrets/token.pickle` が生成される。

### 4. 動作確認
```bash
docker compose run --rm clipflow python -m clipflow.main --lang jp
```

### 5. トークン期限切れ時の再認証
```bash
rm ./secrets/token.pickle
python scripts/auth_youtube.py --secrets ./secrets/client_secrets.json
```

---

## 考慮事項

- `./secrets/` ディレクトリは `.gitignore` で除外されていることを確認する（`client_secrets.json` と `token.pickle` はリポジトリに含めない）
- OAuth 同意画面が「テスト」状態の場合、100ユーザー制限と7日間トークン有効期限がある。本番運用前に「本番環境」へ移行するか、テストユーザーに自分のアカウントを追加する。
