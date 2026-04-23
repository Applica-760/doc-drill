data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}

# ──────────────────────────────────────────────
# ECS Task Execution Role（frontend / backend 共用）
# ECS がコンテナを起動するための権限
# ──────────────────────────────────────────────
resource "aws_iam_role" "task_execution" {
  name = "${var.project}-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "task_execution_managed" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Secrets Manager からDB接続情報を取得する権限
resource "aws_iam_role_policy" "task_execution_secrets" {
  name = "secrets-manager-read"
  role = aws_iam_role.task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "secretsmanager:GetSecretValue"
      Resource = "arn:aws:secretsmanager:${var.aws_region}:${local.account_id}:secret:${var.project}/db-password*"
    }]
  })
}

# ──────────────────────────────────────────────
# Backend Task Role（FastAPI コンテナ自身の権限）
# ──────────────────────────────────────────────
resource "aws_iam_role" "backend_task" {
  name = "${var.project}-backend-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# S3: PDF の保存・取得・削除
resource "aws_iam_role_policy" "backend_s3" {
  name = "s3-access"
  role = aws_iam_role.backend_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
        ]
        Resource = "arn:aws:s3:::${var.project}-${local.account_id}/documents/*"
      },
      {
        Effect   = "Allow"
        Action   = "s3:ListBucket"
        Resource = "arn:aws:s3:::${var.project}-${local.account_id}"
        Condition = {
          StringLike = { "s3:prefix" = "documents/*" }
        }
      },
    ]
  })
}

# Bedrock: Claude 呼び出し（クロスリージョン推論プロファイル経由）
resource "aws_iam_role_policy" "backend_bedrock_invoke" {
  name = "bedrock-invoke-model"
  role = aws_iam_role.backend_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = "bedrock:InvokeModel"
      Resource = [
        # foundation model 直接呼び出し（東京）
        "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-*",
        # jp.* クロスリージョン推論プロファイル（東京）
        "arn:aws:bedrock:${var.aws_region}:${local.account_id}:inference-profile/jp.anthropic.claude-*",
        # jp.* プロファイルが実際にルーティングする大阪リージョンの foundation model
        "arn:aws:bedrock:ap-northeast-3::foundation-model/anthropic.claude-*",
      ]
    }]
  })
}

# Bedrock Knowledge Bases: PDF 登録（Ingestion）・類似検索（Retrieve）
# KB ARN は Step 8（bedrock モジュール）で確定するため、現時点では * で許可しスコープを絞る
resource "aws_iam_role_policy" "backend_bedrock_kb" {
  name = "bedrock-knowledge-base"
  role = aws_iam_role.backend_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:StartIngestionJob",
          "bedrock:GetIngestionJob",
        ]
        Resource = "arn:aws:bedrock:${var.aws_region}:${local.account_id}:knowledge-base/*"
      },
      {
        Effect   = "Allow"
        Action   = "bedrock:Retrieve"
        Resource = "arn:aws:bedrock:${var.aws_region}:${local.account_id}:knowledge-base/*"
      },
    ]
  })
}
