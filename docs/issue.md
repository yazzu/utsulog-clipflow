# 残りの検討事項

## 未実装・未設計

### systemd.timer 設定
- JP向け（19:00 JST）・EN向け（19:00 EST）のタイマーユニットファイルを作成していない
- 実行コマンド: `docker compose run --rm clipflow python -m clipflow.main --lang jp`
- `docker-compose.yml` に `command` が未定義のため、timer から起動する際にコマンドを明示する必要がある

### TikTok API の動作確認
- `tiktok.py` で返す `publish_id` を `tt_id` として扱っているが、TikTok API の実仕様で `publish_id` が永続的な動画識別子として使えるか未確認
- アップロード完了後のステータス確認 API（`/v2/post/publish/status/fetch/`）の呼び出しが未実装
- アクセストークンのリフレッシュ処理が未実装

---

## コードの改善余地（コードレビュー指摘）

### Dockerfile・requirements のテスト依存分離
- 現状、`moto[s3]` と `pytest` が本番イメージの `requirements.txt` に含まれている
- `requirements-dev.txt` を分離し、Dockerfile をマルチステージビルドにすることでイメージサイズ削減とアタックサーフェス低減が可能

### Dockerfile のセキュリティ
- コンテナ内プロセスが root 権限で動作している
- `useradd` + `USER` ディレクティブで非 root ユーザーに切り替えることを推奨

### `highlight_id` 抽出ロジックの脆弱性
- `main.py` での `"_".join(stem.split("_")[:-1])` はファイル名に追加のアンダースコアが入ると壊れる
- `post_metadata.ndjson` に `highlight_id` フィールドを追加するか、正規表現による明示的なパースを検討

### `test_main.py` の tt_id 検証欠落
- `test_run_both_fail_stays_pending` で `tt_id` の最終値が assert されていない

---

## 運用上の未決事項

### S3 バックアップの IAM 権限設定
- Raspberry Pi 上の AWS 認証情報の管理方法（IAM ロール vs アクセスキー）が未決定

### エラー通知
- 投稿失敗時のアラート手段（メール・Slack 等）が未設計
- 現状は stdout ログのみ

### `partial` レコードの放置対策
- 長期間 `partial` のままになったレコードを検知・通知する仕組みが未設計
