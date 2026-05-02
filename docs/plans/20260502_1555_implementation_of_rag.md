# 目的・前提・方針案

`docs/private/plan_iteration1.md`のPhase3に記載のように、RAGパイプラインを自作のものに切り替えたい
このPlanを一部変更し、
- 自作RAGを構築、動作確認
- 最後にシステムとの接続およびKnowledge baseとの分離
を行いたいです

作成済みの計画で考慮が漏れている点を重点的に深掘りしたいです

# 計画

## 方針決定

| 項目 | 決定内容 |
|---|---|
| チャンクサイズ | 500文字、オーバーラップ100文字 |
| アップロード時のRAG処理 | 非同期（FastAPI `BackgroundTasks`） |
| pgvector インデックス型 | HNSW |
| 埋め込み次元数 | 1024（Titan Embed Text v2 デフォルト） |

## Phase 1: ローカルRAGパイプライン構築 ✅ 2026-05-02

- [x] `docker-compose.yml` の DB イメージを `postgres:16-alpine` → `pgvector/pgvector:pg16` に変更
- [x] `document_chunks` テーブル定義（`document_id` FK / `chunk_text` / `embedding vector(1024)` / `chunk_index`）+ Alembic マイグレーション（`CREATE EXTENSION IF NOT EXISTS vector` を先行実行）
- [x] PDF解析・チャンク分割サービス実装（`pypdf`、500文字・100文字オーバーラップ）
- [x] Bedrock Embeddings API 呼び出しサービス実装（`amazon.titan-embed-text-v2:0`、1024次元）
- [x] pgvector 保存・類似検索サービス実装（HNSW インデックス）
- [x] 単体動作確認（スクリプトで parse→embed→store→search が通ること）

## Phase 2: システム接続・KB撤廃

- [ ] アップロードフロー（`routers/documents.py`）を変更：KB呼び出しを削除し、`BackgroundTasks` でRAGパイプライン（parse→embed→store）を非同期実行
- [ ] 問題生成フロー（`services/bedrock.py` の `_generate_with_kb`）を pgvector 類似検索ベースに切り替え
- [ ] `bedrock_kb_enabled` フラグ・`bedrock_kb_id` / `bedrock_kb_data_source_id` 設定を廃止、`services/knowledge_base.py` を削除
- [ ] ドキュメント削除時（`DELETE /documents/{id}`）の `document_chunks` 連鎖削除を実装
- [ ] `Document.kb_document_id` フィールドを削除（Alembicマイグレーション）
- [ ] ローカルE2E確認（PDFアップロード → BackgroundTasks 処理完了 → 問題生成）

## Phase 3: AWS反映

- [ ] Terraform から Bedrock Knowledge Bases / OpenSearch Serverless リソースを削除
- [ ] ECS タスク定義の不要な環境変数を削除（`BEDROCK_KB_ENABLED` / `BEDROCK_KB_ID` / `BEDROCK_KB_DATA_SOURCE_ID`）
- [ ] `terraform apply` → AWS E2E確認（PDFアップロード → 問題生成）
- [ ] `terraform destroy`

# 実行ログ

# 結果