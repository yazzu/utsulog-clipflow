# Python Project: Utsuro Auto Poster

## Goal
Raspberry Pi 5 上で動作する、YouTube/TikTok への動画自動投稿スクリプトを作成する。

## Features
1. Local SSD (pending) 内のフォルダを、タイムスタンプ順に処理する。
2. post_metadata.ndjson を読み込み、ja/en 投稿用のメタ情報を取得する。
3. YouTube Data API v3 および TikTok API を使用して投稿。
4. 投稿成功後、post_metadata.ndjson,ab_test_metadata.ndjson に videoId を追記し、動画と共に S3 バックアップフォルダへ移動（boto3）。
5. ローカルの pending からは削除する。

## Library Requirements
- google-api-python-client (YouTube)
- requests (TikTok API)
- boto3 (AWS S3)
- ndjson (Metadata parsing)

## 3. pending ディレクトリ構造
```text
/home/yazzu709/share/utsulog-clip/
  ├── pending/
  │    └── {yyyyMMdd_HHmm}_{source_id}/
  │         ├── highlight_001_ja.mp4
  │         ├── highlight_001_en.mp4
  │         ├── highlight_002_ja.mp4
  │         ├── highlight_002_en.mp4
  │         ├── highlight_003_ja.mp4
  │         ├── highlight_003_en.mp4
  │         ├── post_metadata.ndjson # 投稿用メタデータ
  │         └── ab_test_metadata.ndjson # ABテスト用メタデータ
```

## 3. S3 ディレクトリ構造
```text
utsulog-clip-bucket/
  └── backup/
       └── {yyyy}/{mm}
            └──  {yyyyMMdd_HHmm}_{source_id}/
```

## 4-1. メタデータ定義 (`ab_test_metadata.ndjson`)
各動画ファイルのA/Bテスト用情報を管理する。

```jsonl
{"highlight_id": "highlight_001", "language": "ja", "source_video_id": "3hqPAjxCLDs", "layout_name": "layout_v1_default", "highlight_rank": 1, "peak_score": 45.2, "duration_sec": 49.7, "subtitle_enabled_count": 8, "subtitle_total_count": 10, "gemini_model": "gemini-2.0-flash", "created_at": "2026-03-22T14:30:00+09:00", "output_file": "output/highlight_001_ja.mp4", "input_props": {}, "video_id": null, "views": null, "watch_time": null}
```

**フィールド定義:**

| フィールド | タイミング | 説明 |
|---|---|---|
| `highlight_id` | 生成時 | ハイライト識別子 |
| `language` | 生成時 | `"ja"` / `"en"` |
| `source_video_id` | 生成時 | アーカイブ元動画の YouTube ID |
| `layout_name` | 生成時 | 使用したレイアウト設定名 |
| `highlight_rank` | 生成時 | ピークスコア順位（1〜3） |
| `peak_score` | 生成時 | チャットスコアのピーク値 |
| `duration_sec` | 生成時 | 実際の出力尺（秒） |
| `subtitle_enabled_count` | 生成時 | 有効化された字幕数 |
| `subtitle_total_count` | 生成時 | 字幕の総数 |
| `gemini_model` | 生成時 | 翻訳に使用した Gemini モデル |
| `created_at` | 生成時 | 生成日時（ISO 8601、JST） |
| `output_file` | 生成時 | 出力ファイルパス |
| `input_props` | 生成時 | Remotion に渡した JSON パラメータ全記録 |
| `yt_id` | 投稿後付与 | 投稿したショート動画の YouTube ID |
| `yt_views` | 投稿後付与 | 再生数 |
| `yt_watch_time` | 投稿後付与 | 視聴時間 |
| `tt_id` | 投稿後付与 | 投稿したショート動画の Tiktok ID |
| `tt_views` | 投稿後付与 | 再生数 |
| `tt_watch_time` | 投稿後付与 | 視聴時間 |

## 4-1. メタデータ定義 (`post_metadata.ndjson`)
動画ファイルを投稿する際に必要なメタデータを管理する。

```jsonl
{"file": "highlight_001_ja.mp4", "lang": "jp", "highlight_no": 1, "title": "...", "description":"...", "tags":["..."], "categoryId":"...", "forKids":false, "status": "pending", "yt_id": "", "tt_id": ""}
{"file": "highlight_001_en.mp4", "lang": "en", "highlight_no": 1, "title": "...", "description":"...", "tags":["..."], "categoryId":"...", "forKids":false, "status": "pending", "yt_id": "", "tt_id": ""}
...
```

**フィールド定義:**

| フィールド | タイミング | 説明 |
|---|---|---|
| `file` | 生成時 | ファイル名 |
| `lang` | 生成時 | 言語 |
| `highlight_no` | 生成時 | ハイライト番号（投稿順のソートキー、値が小さいほど優先） |
| `title` | 生成時 | タイトル |
| `description` | 生成時 | 説明 |
| `tags` | 生成時 | タグ |
| `categoryId` | 生成時 | カテゴリID |
| `forKids` | 生成時 | 子供向けかどうか |
| `status` | 生成時 | ステータス,pending=未投稿,posted=投稿済み |
| `yt_id` | 投稿後付与 | YouTube Video ID |
| `tt_id` | 投稿後付与 | TikTok Video ID |

## 5. 投稿スケジュール
systemd.timerにて以下のタイムゾーン別に実行する。

| ターゲット | タイムゾーン | 現地実行時間 |
| :--- | :--- | :--- |
| **日本向け (JP)** | `Asia/Tokyo` | 19:00 |
| **米国向け (EN)** | `America/New_York` | 19:00 |


