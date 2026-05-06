# 目的・前提・方針案

## 目的
`terraform init / plan / apply` それぞれの実行フローを図式化し、infra層のTerraform理解を深める

## 前提
- 対象は `infra/` 配下の全 `.tf` ファイル（networking / storage / database / alb / ecs / modules/iam）
- `docs/architecture.md` のMermaidシーケンス図と同じ粒度感で、個別リソース単位まで掘り下げる
- 出力先: `docs/terraform-flow.md`（設計ドキュメントとして恒久保存）

## 方針
- セクションを `init / plan / apply` の3つに分け、各フェーズに最適な図式を採用する
- `init`: flowchart（逐次処理）
- `plan`: sequence diagram（CLI ↔ DynamoDB・S3・AWS API の対話）
- `apply`: graph TD（リソース依存グラフ、Wave別並列実行を可視化）

---

## 計画

## Phase 1: 調査
- [x] `infra/` 配下の全 `.tf` ファイルを読み込み、リソース依存関係を把握

## Phase 2: ドキュメント作成
- [x] `docs/terraform-flow.md` を作成（init / plan / apply 各図 + ポイント解説）

---

## 実行ログ

---

## 結果

`docs/infra-dependency.md` を作成。init / plan セクションを削除し、リソース依存グラフ（graph TD / Wave 別）に特化したドキュメントに再構成。`docs/terraform-flow.md` は削除。