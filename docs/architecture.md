# アーキテクチャ設計

> コンポーネント構成の概要は [spec.md](spec.md) の「4. アーキテクチャ構成」を参照。
> このドキュメントでは **Phase 4（AWSインフラ構築）** で必要な「どう作るか」レベルの設計を記録する。

---

## 全体構成図

```
Internet
  │
  ├──[Frontend ALB (Public, :80)]──→ [ECS: Next.js  (:3000)]
  │                                          │ NEXT_PUBLIC_API_URL
  └──[Backend  ALB (Public, :80)]──→ [ECS: FastAPI  (:8000)]
                                              │
                               ┌──────────────┴──────────────┐
                    [RDS PostgreSQL 16]            [Amazon Bedrock]
                    (DB Subnetに隔離)              ├── Knowledge Bases
                                                   └── Claude (invoke_model)
                                                          ↑
                                                       [S3]
                                                  (PDF保存 / KBデータソース)
```

---

## ネットワーク設計（VPC）

### 基本情報

| 項目 | 値 |
|---|---|
| リージョン | ap-northeast-1 |
| VPC CIDR | 10.0.0.0/16 |
| AZ | ap-northeast-1a / ap-northeast-1c（2AZ構成） |

### サブネット一覧

| 名前 | CIDR | AZ | 用途 |
|---|---|---|---|
| public-a | 10.0.0.0/24 | 1a | ALB、NAT Gateway |
| public-c | 10.0.1.0/24 | 1c | ALB、NAT Gateway |
| private-a | 10.0.10.0/24 | 1a | ECS タスク（frontend / backend） |
| private-c | 10.0.11.0/24 | 1c | ECS タスク（frontend / backend） |
| db-a | 10.0.20.0/24 | 1a | RDS PostgreSQL 16 |
| db-c | 10.0.21.0/24 | 1c | RDS PostgreSQL 16 |

### ルーティング

- Public subnet → Internet Gateway（インターネット直接アクセス）
- Private subnet → NAT Gateway（ECRイメージプル・Bedrock API呼び出しに必要）
- DB subnet → ルートなし（インターネット非接続）

---

## セキュリティグループ設計

| SG名 | インバウンド | 対象 |
|---|---|---|
| frontend-alb-sg | 0.0.0.0/0 → :80 | フロントエンド用ALB |
| backend-alb-sg | 0.0.0.0/0 → :80 | バックエンド用ALB |
| frontend-ecs-sg | frontend-alb-sg → :3000 | Next.js ECSタスク |
| backend-ecs-sg | backend-alb-sg → :8000 | FastAPI ECSタスク |
| db-sg | backend-ecs-sg → :5432 | RDS |

---

## ALB 設計

2つのPublic ALBを用意し、開発・デバッグ時にバックエンドを直接操作できるようにする。

| ALB名 | リスナー | ターゲットグループ | ヘルスチェックパス |
|---|---|---|---|
| doc-drill-frontend | HTTP:80 | Next.js ECS :3000 | `/` |
| doc-drill-backend | HTTP:80 | FastAPI ECS :8000 | `/health` |

> Phase 5 でACM証明書取得後、HTTPS:443リスナーを追加してHTTPをリダイレクトする。

---

## ECR（コンテナレジストリ）

| リポジトリ名 | 対象 |
|---|---|
| doc-drill/frontend | Next.js コンテナイメージ |
| doc-drill/backend | FastAPI コンテナイメージ |

---

## ECS 設計

### クラスター

| 項目 | 値 |
|---|---|
| クラスター名 | doc-drill |
| 起動タイプ | Fargate |

### タスク定義・サービス

#### frontend

| 項目 | 値 |
|---|---|
| タスク定義名 | doc-drill-frontend |
| コンテナポート | 3000 |
| CPU / メモリ | 256 / 512（開発用最小構成） |
| ログ送信先 | CloudWatch: /ecs/doc-drill/frontend |

**環境変数（ECS タスク定義に設定）:**

| 変数 | 値 |
|---|---|
| `NEXT_PUBLIC_API_URL` | `http://{backend-alb-dns}` |
| `HOSTNAME` | `0.0.0.0` |

#### backend

| 項目 | 値 |
|---|---|
| タスク定義名 | doc-drill-backend |
| コンテナポート | 8000 |
| CPU / メモリ | 512 / 1024（Bedrock呼び出しを含むため） |
| ログ送信先 | CloudWatch: /ecs/doc-drill/backend |

**環境変数（ECS タスク定義に設定）:**

| 変数 | 値 | 備考 |
|---|---|---|
| `DATABASE_URL` | Secrets Manager参照 | IAMで取得、平文設定不可 |
| `S3_BUCKET` | `doc-drill-{account_id}` | |
| `AWS_DEFAULT_REGION` | `ap-northeast-1` | |
| `BEDROCK_KB_ENABLED` | `true` | |
| `BEDROCK_KB_ID` | Terraform output | |
| `BEDROCK_KB_DATA_SOURCE_ID` | Terraform output | |

**設定しない変数（ローカルとの差分）:**

| 変数 | 理由 |
|---|---|
| `S3_ENDPOINT_URL` | 実S3はエンドポイント指定不要 |
| `AWS_ACCESS_KEY_ID` | IAMタスクロールで自動解決 |
| `AWS_SECRET_ACCESS_KEY` | IAMタスクロールで自動解決 |
| `BEDROCK_AWS_ACCESS_KEY_ID` | IAMタスクロールで自動解決 |
| `BEDROCK_AWS_SECRET_ACCESS_KEY` | IAMタスクロールで自動解決 |

---

## IAM 設計

### ECS タスク実行ロール（Task Execution Role）

両サービス共通。ECSがコンテナを起動するための権限。

| ポリシー | 用途 |
|---|---|
| `AmazonECSTaskExecutionRolePolicy` | ECRからのイメージプル・CloudWatch Logsへの書き込み |
| `secretsmanager:GetSecretValue` | DB接続情報の取得（Secrets Manager） |

### バックエンド タスクロール（Task Role）

FastAPIコンテナ自身がAWSサービスを呼び出すための権限。

| アクション | リソース | 用途 |
|---|---|---|
| `s3:GetObject` `s3:PutObject` `s3:DeleteObject` `s3:ListBucket` | doc-drillバケット | PDF保存・取得・削除 |
| `bedrock:InvokeModel` | claude モデルARN | 問題生成 |
| `bedrock:StartIngestionJob` `bedrock:GetIngestionJob` | Knowledge Base ARN | PDF登録 |
| `bedrock:Retrieve` | Knowledge Base ARN | 類似チャンク検索 |

### フロントエンド タスクロール

Next.jsはバックエンドをHTTPで呼ぶだけのためAWSサービス呼び出しなし。タスクロール不要（Execution Roleのみ）。

---

## S3 設計

| 項目 | 値 |
|---|---|
| バケット名 | `doc-drill-{aws_account_id}`（グローバル一意性のためaccount_idをサフィックスに） |
| パブリックアクセス | 全てブロック |
| 用途 | PDF保存（`documents/` プレフィックス）、Bedrock KBデータソース |

---

## RDS 設計

| 項目 | 値 |
|---|---|
| エンジン | postgres |
| バージョン | 16.6 |
| インスタンスクラス | db.t3.micro |
| ストレージ | 20GB (gp2) |
| サブネットグループ | db-a / db-c |
| セキュリティグループ | db-sg |
| マスターパスワード | Secrets Manager で管理 |

**Secrets Manager シークレット名:** `doc-drill/db-password`

---

## Bedrock Knowledge Bases 設計

| 項目 | 値 |
|---|---|
| 埋め込みモデル | `amazon.titan-embed-text-v2:0` |
| ベクターストア | Bedrock マネージド（OpenSearch Serverless） |
| データソース | S3バケット（`documents/` プレフィックス） |
| チャンク戦略 | デフォルト（Bedrockに委譲） |

> Phase 6でKnowledge Basesを切り離し、pgvector（RDS）を使った自作パイプラインに置き換える。

---

## Terraformステート管理

### バックエンド構成

ステートファイルをS3に保存し、DynamoDBで同時実行ロックを管理する。

| リソース | 名前 | 備考 |
|---|---|---|
| S3バケット | `doc-drill-tfstate-{account_id}` | バージョニング有効 |
| DynamoDBテーブル | `doc-drill-tfstate-lock` | パーティションキー: `LockID` (String) |

**重要:** これらは Terraform 管理外で**手動作成**する（ステートを保存する場所自体はTerraformで管理できないため）。

作成手順:
```bash
# S3バケット
aws s3api create-bucket \
  --bucket doc-drill-tfstate-{account_id} \
  --region ap-northeast-1 \
  --create-bucket-configuration LocationConstraint=ap-northeast-1

aws s3api put-bucket-versioning \
  --bucket doc-drill-tfstate-{account_id} \
  --versioning-configuration Status=Enabled

# DynamoDB テーブル
aws dynamodb create-table \
  --table-name doc-drill-tfstate-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-northeast-1
```

### backend.tf の記述例

```hcl
terraform {
  backend "s3" {
    bucket         = "doc-drill-tfstate-{account_id}"
    key            = "doc-drill/terraform.tfstate"
    region         = "ap-northeast-1"
    dynamodb_table = "doc-drill-tfstate-lock"
    encrypt        = true
  }
}
```

---

## Terraform ディレクトリ構成

```
infra/
├── versions.tf       # terraform / provider バージョン固定
├── main.tf           # 各モジュールの呼び出し
├── variables.tf      # 入力変数定義
├── outputs.tf        # KB IDなど後続で必要な値を出力
├── terraform.tfvars  # 実際の値（.gitignore 対象）
├── backend.tf        # S3バックエンド宣言（値は backend.hcl に分離）
├── networking.tf     # VPC, サブネット, IGW, NAT GW, ルートテーブル, SG（terraform-aws-modules/vpc）
├── database.tf       # RDS PostgreSQL 16, Secrets Manager（terraform-aws-modules/rds）
├── storage.tf        # S3バケット
├── alb.tf            # ALB 2つ, ターゲットグループ, リスナー（terraform-aws-modules/alb）
├── ecs.tf            # クラスター, タスク定義, サービス（terraform-aws-modules/ecs）
└── modules/
    ├── iam/          # Task Execution Role, Backend Task Role（カスタム）
    └── bedrock/      # Knowledge Base, データソース（カスタム）
```

---

## ローカル vs AWS 環境差分サマリ

| コンポーネント | ローカル | AWS |
|---|---|---|
| オブジェクトストレージ | MinIO（Docker） | Amazon S3 |
| DB | PostgreSQL 16（Docker） | RDS PostgreSQL 16（db.t3.micro） |
| AWS認証 | 環境変数（access key） | IAMタスクロール |
| Bedrock KB | 無効（`BEDROCK_KB_ENABLED=false`） | 有効 |
| バックエンドURL | `http://localhost:8000` | `http://{backend-alb-dns}` |
| DB接続情報 | `.env` ファイル | Secrets Manager |
