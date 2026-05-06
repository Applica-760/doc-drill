> **⚠️ 手順メモ**: このファイルは次セッションへの引き継ぎ用の手順メモです。実装着手前に Claude に渡し、各 Step を順に読解しながら不明点を都度質問してください。Claude はこのファイルの計画に沿って回答・補足します。

---

# 目的・前提・方針案

## 目的
`docs/infra-dependency.md` のMermaidグラフはTerraformのresource参照依存（apply順序・outputs参照）を示しているが、粒度が細かすぎてランタイムの流れが把握しにくい。
代わりにネットワークトポロジー図（VPC層構造・ALB・ECS・IAM・ストレージの配置）を `architecture.md` に追記し、インフラ構成理解の補助とする。

## 発想の経緯
`20260504_1730_system_overview_update` タスクのinfra読解中（2026-05-06）に、`alb.tf` の属性解読をしていた際に発想。
「ALBの"port 80をListenしてport 3000に転送"のような関係はシーケンス図に書きやすい」という気づきから。
→ 検討の結果、リクエスト経路はRAGパイプラインのシーケンス図と重複するため、構造的な配置を示すトポロジー図に方針転換。

## 方針
- `docs/infra-dependency.md` を廃止（削除）。Terraform依存グラフは粒度が細かく、構成理解の補助にならない
- `architecture.md` に追記（ドキュメントを増やさず一元化）
- Draw.io でネットワークトポロジー図を作成（`system-overview.svg` と同じ方針）
- 縦方向（top-to-bottom）で統一：Public subnet → Private subnet → DB subnet の層構造を上から下に配置
- 図の内容：VPC・サブネット・ALB・ECSクラスタ（frontend/backend task）・IAMロール・RDS・S3・Bedrock

---

# 計画

## Phase 1: infra-dependency.md 廃止
- [x] `docs/infra-dependency.md` を削除する

## Phase 2: ネットワークトポロジー図を作成・追記
- [x] Draw.io でネットワークトポロジー図を作成し `docs/assets/infra-network.svg` にエクスポート
  - 縦方向（top-to-bottom）、`system-overview.svg` と統一
  - 構成要素: VPC / Public subnet（ALB×2）/ Private subnet（ECS frontend・backend task）/ DB subnet（RDS）/ AWS Managed（S3・Bedrock・ECR・Secrets Manager）
  - IAMロール: Execution Role（ECR・Secrets Managerへの点線）、backend Task Role（S3・Bedrockへの点線）
- [x] `architecture.md` の「全体構成図（コンポーネント）」直後に図を追記
  - `![ネットワークトポロジー](assets/infra-network.svg)` で参照

---

# 実行ログ

---

# 結果

- `docs/infra-dependency.md` 削除
- `docs/assets/infra-network.svg`（Draw.io）作成
- `architecture.md` に「ネットワークトポロジー」セクション追記
- 検討過程でシーケンス図→トポロジー図に方針転換。RDBがVPC内/AWSマネージドの二面性を持つ点はsystem-overviewとinfra-networkで視点が異なる（コンポーネント vs ネットワーク）ものとして許容