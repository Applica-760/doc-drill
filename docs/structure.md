# プロジェクト構造マップ

## トップレベル

| パス | 役割 |
|------|------|
| `backend/` | FastAPI アプリ・Alembic マイグレーション |
| `frontend/` | Next.js アプリ（アップロード・問題生成・クイズフロー実装済み） |
| `infra/` | Terraform（VPC・RDS・ECS・Bedrock 等、実装済み） |
| `docs/` | 設計・仕様ドキュメント |
| `docker-compose.yml` | ローカル開発用コンテナ定義（backend/frontend/db/minio） |

## エントリポイント

| レイヤー | ファイル |
|----------|---------|
| backend | `backend/app/main.py` |
| frontend | `frontend/src/app/page.tsx` |
| DB マイグレーション | `backend/alembic/versions/` |
| 環境変数定義 | `backend/app/core/config.py` |

## 作業前に読むドキュメント

| 作業 | 参照先 |
|------|-------|
| backend を修正・追加する | [backend 構造詳細](structure-backend.md) |
| frontend を修正・追加する | [frontend 構造詳細](structure-frontend.md) |
| infra を修正・追加する | [infra 構造詳細](structure-infra.md) |
| AWS 構成を検討・変更する | [アーキテクチャ](architecture.md) |
| 技術選定の経緯を確認する | [技術選定](adr.md) |
| API 仕様を確認する | [仕様](spec.md) |
