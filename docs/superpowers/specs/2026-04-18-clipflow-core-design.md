# ClipFlow コア処理フロー 設計ドキュメント

**作成日:** 2026-04-18  
**対象:** YouTube / TikTok 自動投稿スクリプト（コア処理フロー）

---

## 概要

Raspberry Pi 5 上の Docker コンテナで動作する Python スクリプト群。  
`pending` ディレクトリ内の動画ファイルを1本ずつ YouTube / TikTok に投稿し、成功後に S3 へバックアップする。

---

## ディレクトリ構成

```
/home/yazzu709/utsulog-clipflow/
  clipflow/
    main.py              # エントリポイント（--lang jp/en 引数）
    folder_selector.py   # フォルダ・ファイル選択
    metadata.py          # ndjson 読み書き
    youtube.py           # YouTube Data API v3 投稿
    tiktok.py            # TikTok API 投稿
    storage.py           # S3バックアップ・ローカル削除
  tests/
    test_folder_selector.py
    test_metadata.py
    test_storage.py
    fixtures/
      20260412_2233_3hqPAjxCLDs/
        post_metadata.ndjson
        ab_metadata.ndjson
        highlight_001_ja.mp4
        highlight_001_en.mp4
        highlight_002_ja.mp4
        highlight_002_en.mp4
        highlight_003_ja.mp4
        highlight_003_en.mp4
  Dockerfile
  docker-compose.yml
  .env
  .env.example
  requirements.txt
  docs/
    project.md
```

---

## 環境設定

### `.env` 管理（`python-dotenv` 使用）

```env
PENDING_DIR=/data/pending
S3_BUCKET=utsulog-clip-bucket
S3_PREFIX=backup
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=ap-northeast-1
YOUTUBE_CLIENT_SECRETS_FILE=/secrets/client_secrets.json
TIKTOK_ACCESS_TOKEN=...
```

### Docker 構成

- ベースイメージ: `python:3.12-slim`
- `docker-compose.yml` でボリュームマウント（`PENDING_DIR`、YouTube認証ファイル）
- `env_file: .env` で環境変数を注入

---

## 処理フロー（`main.py`）

```
$ python main.py --lang jp   # または --lang en

1. folder_selector.get_oldest_folder(PENDING_DIR)
   → タイムスタンプ ({yyyyMMdd_HHmm}_{source_id}) 昇順で最古フォルダを取得

2. folder_selector.get_next_file(folder, lang)
   → post_metadata.ndjson を highlight_no 昇順で読み込み
   → 指定 lang のみフィルタ
   → status=pending → partial の優先順で1件返す
   → 該当ファイルがなければ None（正常終了）

3. status=partial のレコードは既取得のIDをスキップして欠けているプラットフォームのみ投稿する
   youtube.upload(file_path, record) → yt_id または例外  （yt_id が空の場合のみ実行）
   tiktok.upload(file_path, record) → tt_id または例外  （tt_id が空の場合のみ実行）
   （順次実行、例外をキャッチして部分成功を判定）

4. metadata.update_post_metadata(folder, file, yt_id, tt_id)
   → 両成功: status=posted、yt_id / tt_id を書き込み
   → 片方失敗: status=partial、成功分のIDのみ書き込み
   → 両失敗: status=pending のまま変更なし

   metadata.update_ab_metadata(folder, highlight_id, lang, yt_id, tt_id)
   → ab_metadata.ndjson の該当レコードに yt_id / tt_id を追記（部分成功時も実行）

5. 両成功時のみ:
   storage.backup_file(file_path, folder_name)
   → S3: backup/{yyyy}/{mm}/{folder_name}/ へアップロード
   storage.delete_file(file_path)
   → ローカルファイルを削除
   storage.cleanup_folder_if_empty(folder)
   → フォルダ内に動画ファイルが残っていなければフォルダを削除
```

---

## モジュール定義

### `folder_selector.py`

| 関数 | 引数 | 戻り値 | 説明 |
|---|---|---|---|
| `get_oldest_folder` | `pending_dir: str` | `Path \| None` | タイムスタンプ昇順で最古のフォルダパスを返す。なければ None |
| `get_next_file` | `folder: Path, lang: str` | `dict \| None` | post_metadata のレコードを1件返す。なければ None |

**`get_next_file` の選択優先順位:**
1. `lang` が一致するレコードのみ対象（`"jp"` / `"en"`、`--lang` 引数の値と完全一致）
2. `highlight_no` 昇順
3. `status` が `pending` → `partial` の順

`partial` レコードを選択した場合、`yt_id` / `tt_id` のうち空のものだけ投稿を試みる。

---

### `metadata.py`

| 関数 | 引数 | 説明 |
|---|---|---|
| `read_post_metadata` | `folder: Path` | `post_metadata.ndjson` をパースしてリスト返却 |
| `write_post_metadata` | `folder: Path, records: list` | リストを ndjson に上書き |
| `update_post_metadata` | `folder: Path, file: str, yt_id: str \| None, tt_id: str \| None` | 対象レコードのID・ステータスを更新して書き戻し |
| `update_ab_metadata` | `folder: Path, highlight_id: str, lang: str, yt_id: str \| None, tt_id: str \| None` | `ab_metadata.ndjson` の該当レコードに yt_id / tt_id を追記 |

**ファイル名:**
- `post_metadata.ndjson`
- `ab_metadata.ndjson`（`ab_test_metadata.ndjson` ではない）

**`ab_metadata.ndjson` への書き込みフィールド:**  
`project.md` のフィールド定義に従い `yt_id` / `tt_id` を新規追記する（既存の `video_id` フィールドは変更しない）。

---

### `youtube.py`

| 関数 | 引数 | 戻り値 | 説明 |
|---|---|---|---|
| `upload` | `file_path: Path, record: dict` | `str` (yt_id) | YouTube Data API v3 でショート動画を投稿。失敗時は例外をスロー |

- 認証: `YOUTUBE_CLIENT_SECRETS_FILE` の OAuth2 クライアントシークレットを使用
- `record` から `title`, `description`, `tags`, `categoryId`, `forKids` を取得

---

### `tiktok.py`

| 関数 | 引数 | 戻り値 | 説明 |
|---|---|---|---|
| `upload` | `file_path: Path, record: dict` | `str` (tt_id) | TikTok API で動画を投稿。失敗時は例外をスロー |

- 認証: `TIKTOK_ACCESS_TOKEN` 環境変数を使用

---

### `storage.py`

| 関数 | 引数 | 説明 |
|---|---|---|
| `backup_file` | `file_path: Path, folder_name: str` | S3 の `backup/{yyyy}/{mm}/{folder_name}/` へアップロード |
| `delete_file` | `file_path: Path` | ローカルファイルを削除 |
| `cleanup_folder_if_empty` | `folder: Path` | 動画ファイル（*.mp4）が残っていなければフォルダを削除 |

- `yyyy` / `mm` はフォルダ名 `{yyyyMMdd_HHmm}_{source_id}` のタイムスタンプから抽出

---

## エラー処理

| シナリオ | 挙動 |
|---|---|
| YouTube成功・TikTok失敗 | `status=partial`、`yt_id` のみ書き込み、S3移動なし |
| YouTube失敗・TikTok成功 | `status=partial`、`tt_id` のみ書き込み、S3移動なし |
| 両方失敗 | `status=pending` のまま変更なし、次回リトライ |
| S3アップロード失敗 | ローカルファイル保持、ERRORログ出力、exit 0 |
| ndjson 読み込みエラー | ERRORログ出力、exit 0 |
| pending フォルダなし | INFOログ出力、exit 0 |
| 対象ファイルなし（全件posted） | INFOログ出力、exit 0 |

リトライはスクリプト内では行わない。systemd.timer の定期実行がリトライ機構を兼ねる。

---

## ロギング

- Python 標準 `logging` モジュール使用
- 出力先: stdout（`docker logs` で確認）
- ログレベル: `INFO`（通常フロー）/ `WARNING`（partial）/ `ERROR`（投稿失敗・ファイル異常）

---

## テスト方針

| モジュール | テスト方法 |
|---|---|
| `folder_selector` | 一時ディレクトリにフォルダ・ndjson を作成してユニットテスト |
| `metadata` | `tests/fixtures/` の ndjson を使用してユニットテスト |
| `storage` | `moto` ライブラリで S3 をモック |
| `youtube` / `tiktok` | `unittest.mock` で API 呼び出しをモック |
| `main` | 各モジュールをモックして統合フローをテスト |

### テスト実行

```bash
docker compose run --rm clipflow python -m pytest tests/
```

---

## systemd.timer 呼び出し

```bash
# JP向け (19:00 JST)
docker compose run --rm clipflow python main.py --lang jp

# EN向け (19:00 EST)
docker compose run --rm clipflow python main.py --lang en
```

---

## ライブラリ

```
google-api-python-client   # YouTube Data API v3
requests                   # TikTok API
boto3                      # AWS S3
python-dotenv              # .env 読み込み
moto[s3]                   # テスト用 S3 モック
pytest                     # テストフレームワーク
```
