# 技術選定

## Terraform

**理由**
- HCLはAWS固有でなく汎用的なスキルとして習得価値が高い
- `terraform-aws-modules` によりVPC・ECSなどの標準構成をベストプラクティスに沿って学べる
- CDKはアプリコードと同言語になるため、インフラ学習の文脈で責務が混在しやすい

**トレードオフ**
- CDKに比べ型安全性が低い
- AWS新サービスへの対応がCDKより遅れることがある

---

## Amazon Bedrock

**理由**
- Bedrock Knowledge Bases・Embeddings・ECS・S3・IAMを組み合わせることで、AWSサービス間連携を一貫して学べる
- LLM・埋め込み・RAGをAWS内で完結させることで、インフラ設計の見通しが良くなる
- Phase 6でKnowledge Basesを切り離し自作RAGパイプライン（pgvector）に置き換えることで、マネージドサービスと自作実装の対比も学べる

**トレードオフ**
- OpenAI APIに比べてモデルの選択肢・ドキュメントの量が少ない
- ローカル開発時はAWS認証が必要

---

## Next.js

**理由**
- フルスタック構成における現在のデファクトスタンダードであり、習得優先度が高い
- App RouterによるSSR・ルーティングの設計パターンを実践できる
- ECS Fargateへのコンテナデプロイを通じ、フロントエンドのインフラ側も学べる

**トレードオフ**
- 本アプリの規模にはオーバースペックであり、Viteで十分な側面がある

---

## FastAPI

**理由**
- Bedrock SDK（boto3）・PDF処理など、AI関連ライブラリとの親和性が高い
- 非同期対応・自動スキーマ生成（OpenAPI）を備え、実用的なAPIサーバとして十分な機能を持つ
- Hono.jsはTypeScriptで統一できる利点があるが、Bedrock連携の文脈ではPythonが適切

**トレードオフ**
- フロントと言語が分かれるため、型定義の共有には工夫が必要

---

## Docker

**理由**
- ローカルでDocker Composeを使うことで、ECS Fargateへのデプロイ時の環境差異を減らせる
- フロント・バック・DBを単一の `compose.yml` で管理することで、インフラ構成の全体像を把握しやすい
- コンテナ化の実践はECR・ECSの理解に直結する

**トレードオフ**
- 仮想環境に比べローカル開発の初期セットアップが複雑になる

---

## ローカルDB: PostgreSQL 16（Dockerコンテナ）

**理由**
- 本番のAurora Serverless v2がPostgreSQL 15/16互換であるため、ローカルでもバージョンを揃えることでSQL構文・関数の挙動差異を防げる
- ローカルでAuroraに直接接続するとコスト・インターネット依存・起動速度の問題があるため、互換DBをコンテナで代替する
- アプリコードは接続先URLの環境変数を切り替えるだけで、ローカル↔本番を同一コードで動作させられる

**トレードオフ**
- Aurora固有の機能（サーバーレスのオートスケール挙動など）はローカルでは再現できない

---

## ローカルオブジェクトストレージ: MinIO（Dockerコンテナ）

**理由**
- 本番のAmazon S3と完全互換のAPIを持つため、boto3等のSDKは`endpoint_url`を差し替えるだけで動作し、アプリコードの変更が不要
- LocalStack（AWSサービス全般のエミュレーター）と比べてS3専用のため軽量・シンプルで、今回S3以外のサービスをローカルエミュレートする必要がない
- ローカルとAWSで同じアーキテクチャパターン（ファイルをオブジェクトストレージに保存し、キーをDBで管理）を体験できる

**トレードオフ**
- IAMポリシーやバケットポリシーの挙動はAWS S3と異なるため、権限設計の検証は実際のAWS環境で行う必要がある

---

## フロントエンドUIの役割分担: Mantine UI + Tailwind CSS

**方針**
- **UIコンポーネント（Mantine）**: Button, Card, Input, Modal, Stepper, Dropzone など、インタラクティブな要素はすべて Mantine のコンポーネントを使用する
- **レイアウト・余白（Tailwind）**: ページ全体のグリッド、コンポーネント間のスペーシング、最大幅制限などのレイアウト調整には Tailwind ユーティリティクラスを使用する

**境界の判断基準**
> 「それは Mantine のコンポーネントで表現できるか？」→ Yes なら Mantine。No（ページ構造・配置・間隔）なら Tailwind。

**理由**
- Mantine コンポーネントに Tailwind のスタイルを混在させるとクラスの優先順位が競合しやすくなるため、責務を明確に分離することで保守性を高める

**トレードオフ**
- Tailwind 単体に比べてバンドルサイズが増加する
- Mantine のテーマとTailwindの設定値（色・breakpoint等）の二重管理が生じる

---

## ローカルDockerランタイム: OrbStack

**理由**
- Docker Desktop比で起動・ビルドが高速、メモリ消費が少ない（特にApple Silicon環境）
- `docker` / `docker compose` CLIは完全互換であり、`Dockerfile`・`docker-compose.yml`はDocker Desktop利用者と共有可能
- OrbStackはあくまでローカルのランタイムであり、成果物（DockerイメージやIaC）に依存関係は生じない

**トレードオフ**
- チーム開発でDocker Desktopが標準の場合、個人環境の差異として認識・説明が必要になる場合がある

---

## API型定義の共有戦略: OpenAPI スキーマ → TypeScript 型自動生成

**方針**
- FastAPI が自動生成する `/openapi.json` を唯一の真実（Single Source of Truth）とする
- `openapi-typescript` を使って TypeScript 型ファイル（`src/lib/api.gen.ts`）を生成する
- `api.gen.ts` はコミット対象とし、手動編集禁止とする
- バックエンドのスキーマ変更時は `npm run generate:api` を手動で実行してコミットに含める

**理由**
- フロントとバックで言語が異なる（TypeScript / Python）ため、型定義ファイルの直接共有はできない
- FastAPI は Pydantic モデルから OpenAPI スキーマを自動生成するため、中間フォーマットとして活用できる
- 手書きの型定義（`types.ts`）との二重管理を排除し、バック変更時のフロント反映漏れを防ぐ

**自動実行ではなく手動実行を選んだ理由**
- `api.gen.ts` をコミットに含めることで、FastAPI 未起動の環境でもフロントのビルドが通る
- `dev` スクリプトに組み込むと FastAPI 起動が前提になり、フロント単独起動ができなくなる
- 将来 CI で「`generate:api` 後に差分が出たらエラー」とするチェックを入れることで、忘れ防止を自動化できる

**トレードオフ**
- バックのスキーマ変更後に `npm run generate:api` を叩き忘れると不整合が生じる（CI チェックで補完予定）
- FastAPI を起動した状態でないとスクリプトが実行できない

---

## バリデーション制約の二重管理（既知の不整合）

**現状**
- `openapi-typescript` は Pydantic の `Field(ge=1, le=20)` などのバリデーション制約を TypeScript 型に反映しない
- そのため `DocumentSelect.tsx` に `QUESTION_COUNT_MIN=1`, `MAX=20`, `DEFAULT=5` をハードコードしており、`question.py` と手動で同期している

**許容している理由**
- 問題数の上限・下限はアプリの仕様として安定しており、頻繁に変わる値ではない
- openapi-typescript の型生成で解決できる問題ではなく、別途ランタイムバリデーション（zod 等）を導入しないと根本解決にならない
- MVPの範囲ではオーバーエンジニアリングと判断

**将来の対応方針**
- スキーマ変更時は `question.py` の `Field` 制約とフロントの定数を必ずセットで変更する
- 本格的に解決する場合は `zod` + `openapi-zod-client` の導入を検討する
