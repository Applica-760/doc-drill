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

## Phase 2: システム接続・KB撤廃 ✅ 2026-05-02

- [x] アップロードフロー（`routers/documents.py`）を変更：KB呼び出しを削除し、`BackgroundTasks` でRAGパイプライン（parse→embed→store）を非同期実行
- [x] 問題生成フロー（`services/bedrock.py` の `_generate_with_kb`）を pgvector 類似検索ベースに切り替え
- [x] `bedrock_kb_enabled` フラグ・`bedrock_kb_id` / `bedrock_kb_data_source_id` 設定を廃止、`services/knowledge_base.py` を削除
- [x] ドキュメント削除時（`DELETE /documents/{id}`）の `document_chunks` 連鎖削除を実装（ON DELETE CASCADE により自動）
- [x] `Document.kb_document_id` フィールドを削除（Alembicマイグレーション）
- [x] ローカルE2E確認（PDFアップロード → BackgroundTasks 処理完了 → document_chunks 保存確認）

## Phase 3: AWS反映

- [x] `infra/main.tf` から `module "bedrock"` を削除
- [x] `infra/ecs.tf` から `BEDROCK_KB_ENABLED` / `BEDROCK_KB_ID` / `BEDROCK_KB_DATA_SOURCE_ID` を削除
- [x] `infra/outputs.tf` から `bedrock_kb_id` / `bedrock_data_source_id` outputを削除
- [x] `infra/modules/iam/main.tf` から `backend_bedrock_kb` IAMポリシーを削除
- [x] `terraform apply`（KB / AOSS / IAMポリシーをdestroy）
- [x] `infra/modules/bedrock/` ディレクトリを削除
- [x] AWS E2E確認（PDFアップロード → 問題生成）
- [x] `terraform destroy`

# 実行ログ

### 試行 1: ARM64イメージをAMD64 ECSで実行
- 実施内容: `docker build` を `--platform linux/amd64` なしでビルド・プッシュ
- 結果: `exec /usr/bin/sh: exec format error` でECSタスクが起動不可
- 判断: 棄却 → `--platform linux/amd64` 付きでリビルド

### 試行 2: ビルド時に古いキャッシュが混入
- 実施内容: `--no-cache` なしでビルド → alembicマイグレーションが3件（`a0bcac69c59e`）で止まる
- 結果: `source_type` / `document_chunks` / `drop_kb_document_id` の3マイグレーションが未適用
- 判断: 棄却 → `--no-cache --platform linux/amd64` で再ビルド

### 試行 3: Titan Embedのbedrock:InvokeModel権限漏れ
- 実施内容: `modules/iam/main.tf` の `backend_bedrock_invoke` ポリシーが Claude系のみで Titan Embed 未許可
- 結果: RAG ingestionおよび問題生成で `AccessDeniedException`（`amazon.titan-embed-text-v2:0`）
- 判断: 方針変更 → IAMポリシーに Titan Embed ARN を追加して `terraform apply`

### 試行 4: terraform destroy 時のECR/S3非空エラー
- 実施内容: `terraform destroy` 実行
- 結果: ECRにイメージ残存・S3にオブジェクト残存でdestroy失敗
- 判断: 方針変更 → ECRに `repository_force_delete = true` 追加・S3は手動で `aws s3 rm --recursive` 後にdestroy

# 結果

Phase 1〜3 完了。自作RAGパイプライン（pgvector + Bedrock Embeddings）への置き換えおよびAWS E2E確認まで完了。Bedrock Knowledge Bases / OpenSearch Serverlessリソースは撤廃済み。