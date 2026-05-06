# 目的・前提・方針案

RAGパイプライン（pgvector + Titan Embed）への切り替えにより、`docs/assets/architecture.drawio` と `docs/architecture.md` が実装と乖離している。これを現状に合わせて修正する。

あわせて、両ファイルの命名が概念的に衝突しているため改名する。

**方針：**
- `docs/assets/architecture.drawio` → `docs/assets/system-overview.drawio` に改名（役割：コンポーネント間フロー概念図）
- `docs/architecture.md` は変更なし（役割：インフラ詳細仕様）

# 計画

## Phase 1: ファイル改名

- [x] `docs/assets/architecture.drawio` を `docs/assets/system-overview.drawio` に改名

## Phase 2: system-overview.drawio 更新

- [ ] `Knowledge Base` ノード → `Titan Embed` に変更、S3→KB ingestionエッジ削除（手動対応）

## Phase 3: architecture.md 更新

- [x] 全体構成図から `Knowledge Bases` を削除、`pgvector` / `Titan Embed` を追記
- [x] ECS環境変数から `BEDROCK_KB_ENABLED` / `BEDROCK_KB_ID` / `BEDROCK_KB_DATA_SOURCE_ID` を削除
- [x] IAMポリシーから KB権限行（`StartIngestionJob` / `GetIngestionJob` / `Retrieve`）を削除
- [x] `Bedrock Knowledge Bases 設計` セクションを `RAGパイプライン設計` に置き換え
- [x] S3用途の説明から `KBデータソース` を削除
- [x] RDS設計に `pgvector拡張` を追記
- [x] ローカルvsAWS比較表の `Bedrock KB` 行を削除

# 実行ログ

# 結果

Phase 1・3 完了。Phase 2（drawio手動修正）はユーザーが対応。

このセッションで変更したドキュメント一覧：
- `docs/assets/architecture.drawio` → `docs/assets/system-overview.drawio` に改名
- `docs/architecture.md`: KB関連記述を除去、RAGパイプライン設計セクションに置き換え
- `docs/adr.md`: Bedrockセクションを現状に更新、pgvector移行のADRを追加
- `docs/structure-infra.md`: `modules/bedrock/` の記述・KB IAM権限を削除
- `docs/spec.md`: 構成図・`kb_document_id`フィールド・KB委譲の記述を更新
- `docs/private/plan_mvp.md`: Phase 6 を完了（✅ 2026-05-02）マークに更新
- `docs/private/plan_iteration1.md`: Phase 3 を完了（✅ 2026-05-02）マークに更新
