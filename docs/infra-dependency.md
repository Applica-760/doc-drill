# インフラ リソース依存グラフ

各モジュール・リソースの **outputs が他の variables / inputs としてどう参照されているか**を示す。エッジのラベルは参照されている output 名。

```mermaid
graph LR
  RND["random_password.db"]
  VPC["module.vpc"]
  S3["module.s3"]
  ECR_F["module.ecr_frontend"]
  ECR_B["module.ecr_backend"]
  IAM["module.iam"]
  ECS_CL["module.ecs_cluster"]
  CW["aws_cloudwatch_log_group × 2"]
  SM["aws_secretsmanager_secret.db"]

  SG_FA["aws_sg.frontend_alb"]
  SG_BA["aws_sg.backend_alb"]
  SG_FE["aws_sg.frontend_ecs"]
  SG_BE["aws_sg.backend_ecs"]
  SG_DB["aws_sg.db"]

  ALB_F["module.alb_frontend"]
  ALB_B["module.alb_backend"]
  RDS["module.rds"]
  SMV["aws_secretsmanager_secret_version.db"]

  TD_B["aws_ecs_task_definition.backend"]
  TD_F["aws_ecs_task_definition.frontend"]
  SVC_B["aws_ecs_service.backend"]
  SVC_F["aws_ecs_service.frontend"]

  %% VPC outputs
  VPC -->|vpc_id| SG_FA & SG_BA & SG_FE & SG_BE & SG_DB
  VPC -->|"vpc_id / public_subnets"| ALB_F & ALB_B
  VPC -->|database_subnet_group_name| RDS
  VPC -->|private_subnets| SVC_B & SVC_F

  %% SG chain（ingress source として .id を参照）
  SG_FA -->|id| SG_FE
  SG_BA -->|id| SG_BE
  SG_BE -->|id| SG_DB

  %% SG → ALB / RDS / ECS Service
  SG_FA -->|id| ALB_F
  SG_BA -->|id| ALB_B
  SG_DB -->|id| RDS
  SG_FE -->|id| SVC_F
  SG_BE -->|id| SVC_B

  %% random_password
  RND -->|result| RDS & SMV

  %% RDS / SM → SMV（DATABASE_URL の組み立て）
  RDS -->|db_instance_address| SMV
  SM  -->|id| SMV

  %% SM → TD_B（DATABASE_URL の valueFrom 参照）
  SM -->|arn| TD_B

  %% IAM → Task Definitions
  IAM -->|task_execution_role_arn| TD_B & TD_F
  IAM -->|backend_task_role_arn| TD_B

  %% ECR → Task Definitions（image URL）
  ECR_B -->|repository_url| TD_B
  ECR_F -->|repository_url| TD_F

  %% S3 / ALB / CW → Task Definitions（env var として注入）
  S3    -->|s3_bucket_id| TD_B
  ALB_F -->|dns_name| TD_B
  ALB_B -->|dns_name| TD_F
  CW    -->|name| TD_B & TD_F

  %% ALB → ECS Service（ターゲットグループ登録）
  ALB_F -->|target_groups.arn| SVC_F
  ALB_B -->|target_groups.arn| SVC_B

  %% ECS Cluster / Task Definition → ECS Service
  ECS_CL -->|cluster_arn| SVC_B & SVC_F
  TD_B   -->|arn| SVC_B
  TD_F   -->|arn| SVC_F
```

## 依存関係のポイント

**SG チェーン（ingress source に別 SG の id を使う）**
`frontend_ecs_sg` のインバウンドルールは `security_groups = [aws_security_group.frontend_alb.id]` で書かれている。SG の id を参照することで ALB 経由のトラフィックだけを許可しつつ、`frontend_alb_sg` の作成完了を Terraform に伝える依存が自動的に生じる。

**ALB の dns_name が Task Definition の env var に注入される**
`module.alb_frontend.dns_name` が backend の `CORS_ORIGINS` に、`module.alb_backend.dns_name` が frontend の `NEXT_PUBLIC_API_URL` に渡される。ALB が完成して DNS 名が確定するまで Task Definition を作れないというクロスモジュール参照の典型例。

**`aws_secretsmanager_secret` と `_version` の分離**
`secret_version.secret_string` に `module.rds.db_instance_address` を埋め込む。RDS 作成前はエンドポイントが確定しないため、領域確保（`secret`）と値格納（`secret_version`）をリソースとして分離している。

**ECR の repository_url は URL だけを渡す**
`aws_ecs_task_definition` の `image` に `module.ecr_backend.repository_url` を参照しているが、Terraform が管理するのはリポジトリ（URL）の存在だけ。イメージの push は CI/CD（GitHub Actions）の責務であり、apply 時点ではイメージが存在しない場合もある。

**`lifecycle { ignore_changes }` の意図**
`aws_ecs_service` に `ignore_changes = [task_definition, desired_count]` を設定し、CI/CD によるローリングデプロイを Terraform が上書きしないようにしている。インフラ管理（Terraform）とデプロイ管理（CI/CD）の責務を分離する設計。
