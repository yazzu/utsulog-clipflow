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
mkdir -p secrets
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
