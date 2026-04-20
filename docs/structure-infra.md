# インフラ構成

Terraform 1.7+ / AWS Provider ~> 5.0 / Random Provider ~> 3.0 / Time Provider ~> 0.9 / Null Provider ~> 3.0

## ディレクトリ構成

```
infra/
├── versions.tf              # Terraform・プロバイダーのバージョン固定
├── backend.tf               # S3バックエンドの部分設定（実値は backend.hcl に委譲）
├── backend.hcl              # バックエンドの実値（gitignore対象）
├── variables.tf             # 入力変数定義（aws_region, project）
├── terraform.tfvars         # 変数の実値（gitignore対象）
├── main.tf                  # 各モジュールの呼び出し
├── outputs.tf               # 全モジュールの出力を集約
├── .terraform.lock.hcl      # プロバイダーバージョンのロックファイル（コミット対象）
└── modules/
    ├── networking/          # VPC・サブネット・IGW・NAT GW・ルートテーブル・SG
    ├── iam/                 # ECS Task Execution Role・Backend Task Role
    ├── s3/                  # S3バケット（PDF保存・Bedrock KBデータソース）
    ├── aurora/              # RDS PostgreSQL・DB Subnet Group・Secrets Manager
    ├── ecr/                 # ECRリポジトリ（frontend / backend）
    ├── alb/                 # ALB・ターゲットグループ・リスナー（frontend / backend）
    ├── ecs/                 # ECS Fargate クラスター・タスク定義・サービス（frontend / backend）
    └── bedrock/             # OpenSearch Serverless + Bedrock Knowledge Base・データソース
```

## 初期化コマンド

バックエンドの値は `backend.hcl` に記述し、以下のコマンドで初期化する。

```bash
terraform init -backend-config=backend.hcl
```

## 各モジュールの責務

### `networking/`

VPC（10.0.0.0/16）とその配下のネットワークリソースをすべて管理する。

| リソース | 概要 |
|---|---|
| `aws_vpc` | ap-northeast-1、DNS解決有効 |
| `aws_subnet` × 6 | public-a/c・private-a/c・db-a/c（各/24） |
| `aws_internet_gateway` | パブリックサブネットのインターネット出口 |
| `aws_eip` + `aws_nat_gateway` | public-a に1台（開発用コスト削減） |
| `aws_route_table` × 3 | public（IGW）・private（NAT GW）・db（ルートなし） |
| `aws_security_group` × 5 | frontend-alb / backend-alb / frontend-ecs / backend-ecs / db |

**出力:** `vpc_id`, `public_subnet_ids`, `private_subnet_ids`, `db_subnet_ids`, 各SG ID

### `iam/`

ECS が必要とする IAM ロールとポリシーを管理する。

| リソース | 概要 |
|---|---|
| `task-execution-role` | ECRプル・CloudWatch Logs書き込み・Secrets Manager読み取り（frontend/backend共用） |
| `backend-task-role` | S3操作・Bedrock InvokeModel・Knowledge Base Ingest/Retrieve |

Bedrockの Knowledge Base ARN は Step 8 確定後に `knowledge-base/*` から実ARNへ絞り込む予定。

**出力:** `task_execution_role_arn`, `backend_task_role_arn`

### `s3/`

PDF保存と Bedrock Knowledge Base のデータソースを兼ねるバケットを管理する。

| リソース | 概要 |
|---|---|
| `aws_s3_bucket` | `doc-drill-{account_id}`（account_idはdataソースで動的取得） |
| `aws_s3_bucket_public_access_block` | パブリックアクセス全ブロック |

**出力:** `bucket_name`, `bucket_arn`

### `aurora/`

> ディレクトリ名は Aurora Serverless v2 を想定していたが、フリーティア制限のため RDS PostgreSQL に変更。

DB接続に必要なリソースをまとめて管理する。

| リソース | 概要 |
|---|---|
| `random_password` | 32文字英数字のマスターパスワード生成（URL安全） |
| `aws_secretsmanager_secret` | `doc-drill/db-password`（recovery_window=0、即時削除可） |
| `aws_secretsmanager_secret_version` | `DATABASE_URL` 形式の接続文字列を格納 |
| `aws_db_subnet_group` | db-a / db-c サブネットグループ |
| `aws_db_instance` | PostgreSQL 16.6 / db.t3.micro / 20GB gp2 / Single-AZ |

ECS タスク定義では `secrets` の `valueFrom` でシークレット ARN を参照し、
`DATABASE_URL` 環境変数としてコンテナに注入する。

**出力:** `db_endpoint`, `database_name`, `secret_arn`

### `ecr/`

frontend / backend の ECR リポジトリを管理する。

| リソース | 概要 |
|---|---|
| `aws_ecr_repository` × 2 | `doc-drill/frontend`, `doc-drill/backend` / scan_on_push 有効 |
| `aws_ecr_lifecycle_policy` × 2 | 最新5件を超えた古いイメージを自動削除 |

**出力:** `frontend_repository_url`, `backend_repository_url`

### `alb/`

frontend / backend それぞれの Application Load Balancer を管理する。

| リソース | 概要 |
|---|---|
| `aws_lb` × 2 | パブリック ALB（frontend:3000 / backend:8000） |
| `aws_lb_target_group` × 2 | `target_type = "ip"`（Fargate awsvpc モード必須）/ deregistration_delay=30s |
| `aws_lb_listener` × 2 | HTTP:80 → 対応 TG へフォワード |

**出力:** `frontend_alb_dns`, `backend_alb_dns`, `frontend_tg_arn`, `backend_tg_arn`

### `ecs/`

ECS Fargate クラスター・タスク定義・サービスを管理する。

| リソース | 概要 |
|---|---|
| `aws_ecs_cluster` | ContainerInsights 有効 |
| `aws_cloudwatch_log_group` × 2 | `/ecs/doc-drill/{backend,frontend}` / retention=7days |
| `aws_ecs_task_definition` (backend) | 512CPU/1024MEM・`DATABASE_URL` を Secrets Manager `valueFrom` で注入 |
| `aws_ecs_task_definition` (frontend) | 256CPU/512MEM・`NEXT_PUBLIC_API_URL` に backend ALB DNS を注入（※SSR用途のみ有効） |
| `aws_ecs_service` × 2 | Fargate / プライベートサブネット / desired_count=1 |

ECS サービスには `lifecycle { ignore_changes = [task_definition, desired_count] }` を設定し、
Phase 5 の CI/CD デプロイと競合しないようにする。

**出力:** `cluster_arn`, `backend_service_name`, `frontend_service_name`

### `bedrock/`

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
