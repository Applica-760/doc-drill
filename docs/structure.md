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

## レイヤー別詳細

| レイヤー | 参照先 |
|------|-------|
| backend | [backend 構造詳細](structure-backend.md) |
| frontend | [frontend 構造詳細](structure-frontend.md) |
| infra | [infra 構造詳細](structure-infra.md) |
