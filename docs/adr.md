# 技術選定

## Terraform

IaCにはTerraformを採用（CDKより汎用的なスキルとして習得価値が高いため）。

**理由**
- HCLはAWS固有でなく汎用的なスキルとして習得価値が高い
- `terraform-aws-modules` によりVPC・ECSなどの標準構成をベストプラクティスに沿って学べる
- CDKはアプリコードと同言語になるため、インフラ学習の文脈で責務が混在しやすい

**トレードオフ**
- CDKに比べ型安全性が低い
- AWS新サービスへの対応がCDKより遅れることがある

---

## NAT Gateway（VPCエンドポイントとのトレードオフ）

プライベートサブネットからの外部アクセスにNAT Gatewayを採用。

**理由**
- VPCエンドポイントより設定がシンプルで、必要なサービスが増えても追加設定不要
- このプロジェクトで必要なInterface Endpoint（ECR×2・Bedrock・Secrets Manager・CloudWatch Logs）を2AZ分作ると月~$58となり、NAT Gateway（月~$45）より高コストになる

**トレードオフ**
- $0.062/時間の固定課金が発生する

---

## Amazon Bedrock

AI推論にはAmazon Bedrockを採用（Claude による問題生成・Titan Embed によるRAG埋め込み）。

**理由**
- ECS・S3・IAMと組み合わせることでAWSサービス間連携を一貫して学べる
- Bedrock Knowledge Basesを自作RAGパイプライン（pgvector）に置き換えることで、マネージドサービスと自作実装の対比を学べた

**トレードオフ**
- OpenAI APIに比べてモデルの選択肢・ドキュメントの量が少ない

---

## RAGパイプライン: pgvector（Bedrock Knowledge Bases からの移行）

ベクトルストアにはpgvectorを採用し、Bedrock Knowledge Bases（OpenSearch Serverless）を撤廃。

**理由**
- OpenSearch Serverlessはindexing/search各2 OCU必須で、ゼロ利用でも約$690/月の固定費が発生する
- pgvectorは既存RDSへの拡張追加のみで導入でき、追加インフラコストがゼロ
- 埋め込み生成（Titan Embed）は従量課金（$0.00002/1,000トークン）のため実利用量に比例したコストになる

**トレードオフ**
- AOSSに比べてスケーラビリティが低い（本プロジェクトの規模では問題なし）
- ingestionの信頼性・リトライ処理を自前で担う必要がある

---

## フロントエンドUIの役割分担: Mantine UI + Tailwind CSS

Mantine UI をインタラクティブコンポーネント、Tailwind CSS をレイアウト・スペーシングに役割分担して併用。

**理由**
- Mantine はボタン・モーダル・Dropzone・Stepper など、状態・アクセシビリティを伴うコンポーネントを網羅しており、スクラッチ実装コストを削減できる
- Tailwind はページ全体のグリッド・最大幅・余白といったレイアウト制御を utility-first で書けるため、Mantine のコンポーネント単位のスタイルが届かない箇所を補完できる

**トレードオフ**
- 2つのスタイルシステムを使うため、スタイルを書く場所の判断基準（コンポーネントの見た目 → Mantine / レイアウト → Tailwind）を意識し続ける必要がある

---

## Next.js

フロントエンドにはNext.jsを採用。

**理由**
- フルスタック構成のデファクトスタンダードとして習得優先度が高い

**トレードオフ**
- 本アプリの規模にはオーバースペックであり、Viteで十分な側面がある

---

## FastAPI

バックエンドにはFastAPIを採用。

**理由**
- Bedrock SDK（boto3）・PDF処理など、AI関連ライブラリとの親和性が高い

**トレードオフ**
- フロントと言語が分かれるため、型定義の共有には工夫が必要

---

## ローカルDB: PostgreSQL 16（Dockerコンテナ）

ローカルDBは本番と同バージョンのPostgreSQL 16をDockerで代替（SQL挙動の差異を防ぐため）。

**理由**
- 本番のRDS PostgreSQL 16と同バージョンを使うことでSQL構文・関数の挙動差異を防げる
- アプリコードは接続先URLの環境変数を切り替えるだけで、ローカル↔本番を同一コードで動作させられる

**トレードオフ**
- RDSの一部マネージド機能（自動バックアップ・Multi-AZフェイルオーバーの挙動等）はローカルでは再現できない

---

## ローカルオブジェクトストレージ: MinIO（Dockerコンテナ）

ローカルオブジェクトストレージにはMinIOを採用（S3互換APIによりアプリコードの変更なしに切り替え可能なため）。

**理由**
- S3と完全互換のAPIを持つため、boto3等のSDKは`endpoint_url`を差し替えるだけで動作し、アプリコードの変更が不要
- LocalStackと比べてS3専用のため軽量・シンプル

**トレードオフ**
- IAMポリシーやバケットポリシーの挙動はAWS S3と異なるため、権限設計の検証は実際のAWS環境で行う必要がある

---

## ローカルDockerランタイム: OrbStack

ローカルDockerランタイムにはOrbStackを採用（Apple Silicon環境での速度・メモリ効率が優れているため）。

**理由**
- Docker Desktop比で起動・ビルドが高速、メモリ消費が少ない（特にApple Silicon環境）
- `docker` / `docker compose` CLIは完全互換であり、成果物（DockerイメージやIaC）に依存関係は生じない

**トレードオフ**
- チーム開発でDocker Desktopが標準の場合、個人環境の差異として説明が必要になる場合がある

---

## API型定義の共有: OpenAPI スキーマ → TypeScript 型自動生成

フロント・バックの型共有にはOpenAPIスキーマからのTypeScript型自動生成を採用（FastAPIのPydanticモデルをSingle Source of Truthとするため）。

**理由**
- FastAPIはPydanticモデルからOpenAPIスキーマを自動生成するため、中間フォーマットとして活用できる
- 手書きの型定義（`types.ts`）との二重管理を排除し、バック変更時のフロント反映漏れを防ぐ
- `api.gen.ts` をコミットに含めることでFastAPI未起動の環境でもフロントのビルドが通る。`dev` スクリプトへの組み込みはフロント単独起動を妨げるため手動実行とした

**トレードオフ**
- バックのスキーマ変更後に `npm run generate:api` を叩き忘れると不整合が生じる（CIチェックで補完予定）
- FastAPIを起動した状態でないとスクリプトが実行できない