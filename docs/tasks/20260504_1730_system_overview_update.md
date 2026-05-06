> **⚠️ 手順メモ**: このファイルは次セッションへの引き継ぎ用の手順メモです。実装着手前に Claude に渡し、各 Step を順に読解しながら不明点を都度質問してください。Claude はこのファイルの計画に沿って回答・補足します。

---

# 目的・前提・方針案

## 目的
MVP〜Iteration 1 を経た現在の実装（自作 RAG パイプライン）に合わせて system overview 図を更新する。
Bedrock Knowledge Bases / OpenSearch Serverless が消え、pgvector + 自作パイプラインに置き換わった差分が主な更新対象。

## 前提
- 現状の図は Bedrock Knowledge Bases ベースの MVP 時点で描かれている可能性がある
- 変更点を把握するにはドキュメント・インフラ・コードの3層を照合する必要がある

## 方針
コードを直接読む前に、ドキュメント → インフラ → コードの順に読んで差分を整理し、最後に図を更新する。
各 Step は順に読解しながら不明点を Claude に質問して進める。

---

## 計画

### Phase 1: 現状ドキュメントの把握
- [x] `docs/architecture.md` を読み、現在の図が何を想定しているか把握する
- [x] `docs/spec.md` を読み、仕様上のデータフロー定義を確認する

### Phase 2: インフラの確認
- [x] `docs/structure-backend.md` を読み、ファイル構成を把握する（Bedrockは残存・KBは廃止。services/の記述を現状に更新済み）
- [ ] `infra/` の `.tf` ファイルを読み、実際に存在する AWS リソースを把握する
  - 消えたリソース: Bedrock Knowledge Bases / OpenSearch Serverless
  - 追加されたリソース: pgvector 拡張（RDS）

### Phase 3: バックエンドのデータフロー読解
- [ ] PDF アップロード → チャンク分割 → 埋め込み生成 → pgvector 保存 の実装ファイルをトレースする
- [ ] 類似検索 → 問題生成 の実装ファイルをトレースする

### Phase 4: 差分整理と図の更新
- [ ] Phase 1〜3 の読解結果をもとに「図と実装の差分」を箇条書きで整理する
- [ ] `docs/architecture.md` の system overview 図を更新する

---

## 実行ログ

### 試行 1: structure-backend.md の Bedrock 記述確認・修正
- 実施内容: `services/` の実ファイルと照合。`bedrock.py` は現役（LLM + Titan Embed）だが、`embeddings.py` / `pdf_parser.py` / `vector_store.py` が未記載だった
- 結果: コメント・責務説明を現状の5ファイル構成に更新
- 判断: 続行

---

## 結果

（未着手）