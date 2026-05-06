# doc-drill

PDF などのドキュメントをアップロードし、RAG を用いて自動生成された問題を解くことで学習を効率化する Web アプリケーション。

## 目的

フルスタック開発・AWSインフラ構築・IaC の実践的な習得を主目的としたプロジェクト。アプリはその「乗り物」と位置づけ、スケーラブルなアーキテクチャ設計に重点を置く。

## 主な機能

- PDF ドキュメントのアップロード・管理
- Bedrock (Claude) による問題・解説の自動生成
- 生成した問題の保存と再演習

## デモ

> APIコスト削減のため、本番環境は常時稼働していません。以下のスクリーンショットで動作イメージをご確認ください。

<div align="center">
  <img src="docs/assets/upload.png" width="30%" alt="ファイルアップロード画面">
  <img src="docs/assets/answer.png" width="30%" alt="出題画面">
  <img src="docs/assets/result.png" width="30%" alt="スコア表示画面">
</div>


## 技術スタック

| レイヤー | 技術 |
|---|---|
| Frontend | Next.js (TypeScript) + Mantine UI |
| Backend | FastAPI (Python) |
| Database | RDS PostgreSQL 16 |
| Storage | Amazon S3 |
| AI / RAG | Amazon Bedrock (Claude + Titan Embed) + pgvector |
| Infra | AWS ECS Fargate, VPC, ALB, IAM |
| IaC | Terraform |
| Dev | Docker, Docker Compose |

## アーキテクチャ概要

![アーキテクチャ図](docs/assets/system-overview.svg)

## ローカル起動

```bash
cp .env.example .env
# .env に POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB / MINIO_ROOT_USER / MINIO_ROOT_PASSWORD を設定
docker compose up --build
```

| サービス | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| MinIO Console | http://localhost:9001 |

> Bedrock 連携（Claude・Titan Embed）はローカルでも動作するが、`BEDROCK_AWS_ACCESS_KEY_ID` の設定が必要。

## ドキュメント

| ドキュメント | 内容 |
|---|---|
| [ロードマップ](docs/roadmap.md) | 実装フェーズ一覧・進捗・今後の計画 |
| [プロジェクト構造](docs/structure.md) | ディレクトリ構成・作業別の参照先ガイド |
| [技術選定](docs/adr.md) | ADR（技術選定の意思決定記録） |
| [アーキテクチャ](docs/architecture.md) | AWS 詳細構成 |
| [仕様](docs/spec.md) | アプリ仕様・APIエンドポイント一覧 |

## ライセンス

MIT
