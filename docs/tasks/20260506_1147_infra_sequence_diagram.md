> **⚠️ 手順メモ**: このファイルは次セッションへの引き継ぎ用の手順メモです。実装着手前に Claude に渡し、各 Step を順に読解しながら不明点を都度質問してください。Claude はこのファイルの計画に沿って回答・補足します。

---

# 目的・前提・方針案

## 目的
`docs/infra-dependency.md` のMermaidグラフはTerraformのresource参照依存（apply順序・outputs参照）を示しているが、粒度が細かすぎてランタイムの流れが把握しにくい。
代わりにリクエスト経路・起動時認証フローをシーケンス図として `architecture.md` に追記し、インフラ理解の補助とする。

## 発想の経緯
`20260504_1730_system_overview_update` タスクのinfra読解中（2026-05-06）に、`alb.tf` の属性解読をしていた際に発想。
「ALBの"port 80をListenしてport 3000に転送"のような関係はシーケンス図に書きやすい」という気づきから。

## 方針
- `docs/infra-dependency.md` を廃止（削除）。Terraform依存グラフは粒度が細かく、ランタイム理解の補助にならない
- `architecture.md` に追記（ドキュメントを増やさず一元化）
- 案A（リクエスト経路）をメイン、案B（ECS起動時フロー）を補足として追記

---

# 計画

## Phase 1: infra-dependency.md 廃止
- [ ] `docs/infra-dependency.md` を削除する

## Phase 2: architecture.md にシーケンス図を追記
- [ ] 案A（メイン）: ユーザリクエスト経路のシーケンス図を追記
  - User → ALB frontend:80 → ECS frontend:3000
  - ECS frontend → ALB backend:80 → ECS backend:8000
  - ECS backend → RDS:5432 / S3 / Bedrock
- [ ] 案B（補足）: ECS起動時フローのシーケンス図を追記
  - ECS → ECR（イメージプル / Execution Role）
  - ECS → Secrets Manager（DB接続情報取得 / Execution Role）
  - ECS task → S3・Bedrock（Task Role）

---

# 実行ログ

---

# 結果

（未着手）