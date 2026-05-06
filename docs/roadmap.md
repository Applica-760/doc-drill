# 実装ロードマップ

## フェーズ一覧

| フェーズ | 内容 | 状態 |
|---|---|---|
| Phase 1 | ローカル開発基盤（Docker Compose, モノレポ構成） | 完了 |
| Phase 2 | バックエンド実装（FastAPI, Bedrock 連携） | 完了 |
| Phase 3 | フロントエンド実装（Next.js） | 完了 |
| Phase 4 | AWSインフラ構築（Terraform） | 完了 |
| Phase 5 | デプロイ・結合確認（ECR push → terraform apply → E2E 動作確認） | 完了 |
| Phase 6 | 自作RAGパイプラインへの置き換え（Bedrock KB 廃止・pgvector 化） | 完了 |
| Phase 7 | ローカル定型問題モード | 完了 |
| Phase 8 | 定型問題セットの作成 | 完了 |
| Phase 9 | Python ツール整備（ruff / mypy） | 未着手 |
| Phase 10 | CI/CD パイプラインの整備（GitHub Actions + ECS 自動デプロイ） | 未着手 |
| Phase 11 | リファクタリング | 未着手 |

---

## Phase 1: ローカル開発基盤 ✅ 2026-04-16

- [x] モノレポ構成の設計
- [x] FastAPI プロジェクトの初期化
- [x] Next.js プロジェクトの初期化
- [x] Docker Compose でフロント・バック・DB のローカル起動環境を構築

## Phase 2: バックエンド実装（FastAPI） ✅ 2026-04-17

- [x] PDF アップロードエンドポイント（S3互換ローカルストレージで代替）
- [x] Bedrock Knowledge Bases へのドキュメント登録処理
- [x] 問題生成エンドポイント（Bedrock Claude 呼び出し）
- [x] 問題・解答の DB 保存エンドポイント
- [x] 単体テストの整備

## Phase 3: フロントエンド実装（Next.js） ✅ 2026-04-17/18

- [x] PDF アップロード画面
- [x] 問題表示・解答フロー
- [x] 問題一覧・再演習画面

## Phase 4: AWSインフラ構築（Terraform） ✅ 2026-04-18〜20

- [x] VPC・サブネット・セキュリティグループ
- [x] IAMロール・ポリシー
- [x] S3バケット
- [x] RDS PostgreSQL 16（Aurora Serverless v2 はフリーティア制限のため変更）
- [x] ECRリポジトリ
- [x] ECS Fargate（バックエンド・フロントエンド）・ALB
- [x] Bedrock Knowledge Bases・S3連携
- [x] terraform-aws-modules を活用した構成リファクタリング

## Phase 5: デプロイ・結合確認 ✅ 2026-04-22

- [x] terraform apply（全リソース起動）
- [x] ECR ログイン & Docker イメージビルド・Push
- [x] ECS サービスの force new deployment
- [x] E2E 動作確認（PDF アップロード → KB 登録 → 問題生成）
- [x] terraform destroy

## Phase 6: 自作RAGパイプラインへの置き換え ✅ 2026-05-02

Bedrock Knowledge Bases（OpenSearch Serverless: $700+/月）を廃止し、pgvector ベースの自作パイプラインに置き換え。

- [x] PDF 解析・チャンク分割（pypdf）
- [x] 埋め込みベクトル生成（Bedrock Embeddings API）
- [x] pgvector（RDS）へのベクトル保存・類似検索
- [x] Terraform 更新（KB/OpenSearch 削除、RDS pgvector 拡張追加）
- [x] AWS 環境での E2E 確認 → terraform destroy

## Phase 7: ローカル定型問題モード ✅ 2026-04-26

- [x] `Document` モデルに `source_type`（`"pdf"` / `"local"`）を追加・Alembic マイグレーション
- [x] `POST /documents/local` エンドポイント（`source_type: "local"` のダミードキュメント生成）
- [x] `POST /documents/{id}/questions/import` エンドポイント（JSON配列を受け取りバリデーション・DB保存）
- [x] フロントのトップページに SegmentedControl でモード切替（PDF / 定型問題）・定型問題タブにインポートフォーム
- [x] テンプレート JSON のダウンロードボタン
- [x] 動作確認（JSON 投入 → 問題一覧表示 → 演習フロー）

## Phase 8: 定型問題セットの作成 ✅ 2026-04-27

- [x] `architecture.md` ベースのインフラ知識問題セット（VPC・ECS・IAM・RDS等）
- [x] `adr.md` ベースの技術選定問題セット（各ADRにつきトレードオフ形式で1問）
- [x] 問題セットを `docs/private/test.json` に70問格納・演習フロー通し確認

## Phase 9: Python ツール整備

CI を組む前提条件。Python に lint/型チェック設定がない状態で CI を組むと「何でも通る CI」になるため先行する（TypeScript 側は `strict: true` + ESLint 設定済みのため対象外）。

- [ ] `backend/pyproject.toml` に ruff（lint）を追加・設定
- [ ] `backend/pyproject.toml` に mypy（型チェック）を追加・設定
- [ ] 既存コードを ruff / mypy が通る状態に修正

## Phase 10: CI/CD パイプラインの整備

Phase 9 完了後に着手。

- [ ] CI: ruff lint・mypy 型チェック・ESLint・ユニットテスト・Docker ビルド
- [ ] CD: ECR へのイメージ push・ECS サービス自動更新（GitHub Actions）

## Phase 11: リファクタリング

CI を安全網として活用しながら修正する。

### 優先度: 高

- [ ] `backend/app/routers/documents.py:33` の `except Exception` を具体的な例外型に絞る
- [ ] HTTP ステータスコードの一貫性を整理（400/500 の混在を解消）
- [ ] `backend/app/services/embeddings.py` のテスト追加
- [ ] frontend のユニットテスト導入（Vitest 等）

### 優先度: 低

- [ ] `backend/app/routers/` 内の Document 取得クエリの共通化（`documents.py:99,132`、`questions.py:24`）
- [ ] `backend/app/services/bedrock.py:22` の `dict` 型を TypedDict 等で具体化

---

## Backlog

- [ ] 出題コンテキストを指定できるようにする（自然言語で RAG 検索クエリを制御）
- [ ] アップロード UI の下に既存資料の一覧を最初から表示する
- [ ] カラーテーマ等、基本的デザインの修正
- [ ] 問題生成中のローディングに「AIが作問中...」等のテキストを追加
- [ ] API 流量制限（ポートフォリオ公開時に対応）
- [ ] ACM 証明書の取得・ALB への HTTPS 設定（ポートフォリオ公開時に対応）