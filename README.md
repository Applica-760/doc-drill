# doc-drill

PDF などのドキュメントをアップロードし、RAG を用いて自動生成された問題を解くことで学習を効率化する Web アプリケーション。

## 目的

フルスタック開発・AWSインフラ構築・IaC の実践的な習得を主目的としたプロジェクト。アプリはその「乗り物」と位置づけ、スケーラブルなアーキテクチャ設計に重点を置く。

## 主な機能

- PDF ドキュメントのアップロード・管理
- Bedrock (Claude) による問題・解説の自動生成
- 生成した問題の保存と再演習
- 学習履歴・理解度の管理

## 技術スタック

| レイヤー | 技術 |
|---|---|
| Frontend | Next.js (TypeScript) |
| Backend | FastAPI (Python) |
| Database | Aurora Serverless v2 (PostgreSQL) + pgvector |
| Storage | Amazon S3 |
| AI / RAG | Amazon Bedrock (Claude, Embeddings, Knowledge Bases) |
| Infra | AWS ECS Fargate, VPC, ALB, IAM |
| IaC | Terraform |
| Dev | Docker, Docker Compose, GitHub Actions |

## アーキテクチャ概要

```
[Browser]
    │
    ▼
[Next.js on ECS Fargate]
    │
    ▼
[FastAPI on ECS Fargate]  ──→  [Amazon S3]
    │                              │
    ├──→ [Aurora Serverless]       │
    │      (pgvector)              │
    │                              ▼
    └──→ [Amazon Bedrock] ←── [Knowledge Bases]
```

## 実装ロードマップ

| フェーズ | 内容 | 状態 |
|---|---|---|
| Phase 1 | ローカル開発基盤（Docker Compose, モノレポ構成） | 進行中 |
| Phase 2 | バックエンド実装（FastAPI, Bedrock 連携） | 未着手 |
| Phase 3 | フロントエンド実装（Next.js） | 未着手 |
| Phase 4 | AWSインフラ構築（Terraform） | 未着手 |
| Phase 5 | デプロイ・CI/CD 整備（MVP 完成） | 未着手 |
| Phase 6 | 自作 RAG パイプラインへの置き換え（pgvector） | 未着手 |

## ローカル起動

> Phase 1 完了後に追記予定

## ライセンス

MIT
