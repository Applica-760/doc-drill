# インフラ構成

Terraform 1.7+ / AWS Provider ~> 5.0 / Random Provider ~> 3.0 / Time Provider ~> 0.9 / Null Provider ~> 3.0

## ディレクトリ構成

networking / storage / database / alb / ecs は `terraform-aws-modules` を使ったフラットな `.tf` ファイル。
カスタムモジュールは `iam/` と `bedrock/` のみ（公式モジュールが存在しない・設計意図を明示したいもの）。

```
infra/
├── versions.tf              # Terraform・プロバイダーのバージョン固定
├── backend.tf               # S3バックエンドの部分設定（実値は backend.hcl に委譲）
├── backend.hcl              # バックエンドの実値（gitignore対象）
├── variables.tf             # 入力変数定義（aws_region, project）
├── terraform.tfvars         # 変数の実値（gitignore対象）
├── main.tf                  # iam・bedrock モジュール呼び出し・データソース定義
├── outputs.tf               # 全体の出力を集約
├── networking.tf            # VPC（terraform-aws-modules/vpc）・セキュリティグループ
├── storage.tf               # S3（terraform-aws-modules/s3-bucket）・ECR（terraform-aws-modules/ecr）
├── database.tf              # RDS PostgreSQL 16（terraform-aws-modules/rds）・Secrets Manager
├── alb.tf                   # ALB × 2（terraform-aws-modules/alb）
├── ecs.tf                   # ECSクラスター・タスク定義・サービス（terraform-aws-modules/ecs）
├── .terraform.lock.hcl      # プロバイダーバージョンのロックファイル（コミット対象）
└── modules/
    ├── iam/                 # ECS Task Execution Role・Backend Task Role（カスタム）
    └── bedrock/             # OpenSearch Serverless + Bedrock Knowledge Base（カスタム）
```

## 初期化コマンド

バックエンドの値は `backend.hcl` に記述し、以下のコマンドで初期化する。

```bash
terraform init -backend-config=backend.hcl
```

## 各ファイル・モジュールの責務

### `networking.tf`

VPC（10.0.0.0/16）とセキュリティグループを管理する。

| リソース | 概要 |
|---|---|
| `module "vpc"` (terraform-aws-modules/vpc) | public/private/db サブネット × 2AZ・IGW・NAT GW（single、コスト削減） |
| `aws_security_group` × 5 | frontend-alb / backend-alb / frontend-ecs / backend-ecs / db |

### `storage.tf`

S3 バケットと ECR リポジトリを管理する。

| リソース | 概要 |
|---|---|
| `module "s3"` (terraform-aws-modules/s3-bucket) | `doc-drill-{account_id}`、パブリックアクセス全ブロック |
| `module "ecr_frontend"` / `module "ecr_backend"` (terraform-aws-modules/ecr) | scan_on_push 有効・最新5件超のイメージを自動削除 |

### `database.tf`

RDS と Secrets Manager を管理する。

| リソース | 概要 |
|---|---|
| `random_password` | 32文字英数字のマスターパスワード生成（URL安全） |
| `module "rds"` (terraform-aws-modules/rds) | PostgreSQL 16.6 / db.t3.micro / 20GB gp2 / Single-AZ |
| `aws_secretsmanager_secret` + `aws_secretsmanager_secret_version` | `doc-drill/db-password`に `DATABASE_URL` 形式で格納 |

ECS タスク定義では `secrets.valueFrom` でシークレット ARN を参照し、`DATABASE_URL` をコンテナに注入する。

### `alb.tf`

frontend / backend それぞれの Application Load Balancer を管理する。

| リソース | 概要 |
|---|---|
| `module "alb_frontend"` / `module "alb_backend"` (terraform-aws-modules/alb) | HTTP:80 リスナー・`target_type = "ip"`（Fargate awsvpc 必須）・deregistration_delay=30s |

### `ecs.tf`

ECS Fargate クラスター・タスク定義・サービスを管理する。

| リソース | 概要 |
|---|---|
| `module "ecs_cluster"` (terraform-aws-modules/ecs) | ContainerInsights 有効 |
| `aws_cloudwatch_log_group` × 2 | `/ecs/doc-drill/{backend,frontend}` / retention=7days |
| `aws_ecs_task_definition` (backend) | 512CPU/1024MEM・`DATABASE_URL` を Secrets Manager `valueFrom` で注入 |
| `aws_ecs_task_definition` (frontend) | 256CPU/512MEM・`NEXT_PUBLIC_API_URL` に backend ALB DNS を注入（SSR用途のみ有効） |
| `aws_ecs_service` × 2 | Fargate / プライベートサブネット / desired_count=1 |

ECS サービスには `lifecycle { ignore_changes = [task_definition, desired_count] }` を設定し、CI/CD デプロイと競合しないようにする。

### `modules/iam/`（カスタム）

ECS が必要とする IAM ロールとポリシーを管理する。

| リソース | 概要 |
|---|---|
| `task-execution-role` | ECRプル・CloudWatch Logs書き込み・Secrets Manager読み取り（frontend/backend共用） |
| `backend-task-role` | S3操作・Bedrock InvokeModel・Knowledge Base `bedrock:StartIngestionJob` / `bedrock:GetIngestionJob` / `bedrock:Retrieve` |

**出力:** `task_execution_role_arn`, `backend_task_role_arn`

### `modules/bedrock/`（カスタム）

OpenSearch Serverless コレクションと Bedrock Knowledge Base を管理する。

| リソース | 概要 |
|---|---|
| `aws_iam_role` (bedrock_kb) | KB サービスロール（S3読み取り・Titan Embed呼び出し・AOSS操作） |
| `aws_opensearchserverless_security_policy` (encryption) | AWS管理キーで暗号化 |
| `aws_opensearchserverless_security_policy` (network) | パブリックアクセス許可（BedRock サービス + Terraform 実行者がAPIアクセスするため） |
| `aws_opensearchserverless_access_policy` | KB サービスロールと Terraform 実行者 IAM プリンシパルにインデックス操作権限を付与 |
| `aws_opensearchserverless_collection` | type=VECTORSEARCH |
| `time_sleep` | コレクション ACTIVE 待機（120s） |
| `null_resource` | `scripts/create_index.py` を呼び出しベクターインデックスを作成（Bedrock KB 作成前に必須） |
| `aws_bedrockagent_knowledge_base` | Titan Embed v2 / OPENSEARCH_SERVERLESS ストレージ |
| `aws_bedrockagent_data_source` | S3バケット `documents/` プレフィックス |

`scripts/create_index.py` は boto3 と標準ライブラリのみで AWS SigV4 署名を実装し、
外部パッケージ不要で動作する。インデックスが既存の場合はスキップする（べき等）。

**出力:** `knowledge_base_id`, `data_source_id`

## Terraform ステート管理

| リソース | 名前 |
|---|---|
| S3バケット | `doc-drill-tfstate-{account_id}` |
| DynamoDBテーブル | `doc-drill-tfstate-lock` |

これらは Terraform 管理外で手動作成済み（ステートを保存する場所自体はTerraformで管理できないため）。

## ローカル変数・パラメータの規約

- プロジェクト名プレフィックス: `var.project`（= `doc-drill`）
- リージョン: `var.aws_region`（= `ap-northeast-1`）
- AWSアカウントID: `data "aws_caller_identity"` で動的取得（モジュール内に閉じる）
- タグ: すべてのリソースに `Name = "${var.project}-{role}"` を付与
