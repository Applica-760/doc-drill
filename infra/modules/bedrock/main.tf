data "aws_caller_identity" "current" {}

locals {
  account_id      = data.aws_caller_identity.current.account_id
  collection_name = "${var.project}-kb"
  index_name      = "bedrock-knowledge-base-default-index"
}

# ──────────────────────────────────────────────
# IAM Role: Bedrock Knowledge Base サービスロール
# ──────────────────────────────────────────────
resource "aws_iam_role" "bedrock_kb" {
  name = "${var.project}-bedrock-kb-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = local.account_id }
        ArnLike      = { "aws:SourceArn" = "arn:aws:bedrock:${var.aws_region}:${local.account_id}:knowledge-base/*" }
      }
    }]
  })
}

resource "aws_iam_role_policy" "bedrock_kb_s3" {
  name = "s3-read"
  role = aws_iam_role.bedrock_kb.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:ListBucket"]
      Resource = [var.s3_bucket_arn, "${var.s3_bucket_arn}/*"]
    }]
  })
}

resource "aws_iam_role_policy" "bedrock_kb_embedding" {
  name = "bedrock-embedding"
  role = aws_iam_role.bedrock_kb.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "bedrock:InvokeModel"
      Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0"
    }]
  })
}

# AOSS のデータ操作権限（KBサービスロール用）
resource "aws_iam_role_policy" "bedrock_kb_aoss" {
  name = "aoss-api-access"
  role = aws_iam_role.bedrock_kb.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "aoss:APIAccessAll"
      Resource = "arn:aws:aoss:${var.aws_region}:${local.account_id}:collection/*"
    }]
  })
}

# ──────────────────────────────────────────────
# OpenSearch Serverless
# ──────────────────────────────────────────────

# 暗号化ポリシー（コレクション作成前に必須）
resource "aws_opensearchserverless_security_policy" "encryption" {
  name = "${var.project}-kb-enc"
  type = "encryption"

  policy = jsonencode({
    Rules = [{
      Resource     = ["collection/${local.collection_name}"]
      ResourceType = "collection"
    }]
    AWSOwnedKey = true
  })
}

# ネットワークポリシー（Bedrock・Terraform実行者からのパブリックアクセスを許可）
resource "aws_opensearchserverless_security_policy" "network" {
  name = "${var.project}-kb-net"
  type = "network"

  policy = jsonencode([{
    Rules = [
      {
        Resource     = ["collection/${local.collection_name}"]
        ResourceType = "collection"
      },
      {
        Resource     = ["collection/${local.collection_name}"]
        ResourceType = "dashboard"
      }
    ]
    AllowFromPublic = true
  }])
}

# データアクセスポリシー（Bedrock KBロール + Terraform実行者）
resource "aws_opensearchserverless_access_policy" "main" {
  name = "${var.project}-kb-access"
  type = "data"

  policy = jsonencode([{
    Rules = [
      {
        Resource     = ["collection/${local.collection_name}"]
        Permission = [
          "aoss:CreateCollectionItems",
          "aoss:DeleteCollectionItems",
          "aoss:UpdateCollectionItems",
          "aoss:DescribeCollectionItems",
        ]
        ResourceType = "collection"
      },
      {
        Resource = ["index/${local.collection_name}/*"]
        Permission = [
          "aoss:CreateIndex",
          "aoss:DeleteIndex",
          "aoss:UpdateIndex",
          "aoss:DescribeIndex",
          "aoss:ReadDocument",
          "aoss:WriteDocument",
        ]
        ResourceType = "index"
      },
    ]
    Principal = [
      aws_iam_role.bedrock_kb.arn,
      data.aws_caller_identity.current.arn,
    ]
  }])
}

# コレクション（暗号化・ネットワーク・アクセスポリシー確立後に作成）
resource "aws_opensearchserverless_collection" "main" {
  name = local.collection_name
  type = "VECTORSEARCH"

  depends_on = [
    aws_opensearchserverless_security_policy.encryption,
    aws_opensearchserverless_security_policy.network,
    aws_opensearchserverless_access_policy.main,
  ]

  tags = { Name = "${var.project}-kb-collection" }
}

# コレクションが ACTIVE になるまで待機（通常 1〜3 分）
resource "time_sleep" "wait_collection_active" {
  depends_on      = [aws_opensearchserverless_collection.main]
  create_duration = "120s"
}

# ベクターインデックス作成（Bedrock KB はインデックスが存在しないと作成に失敗する）
resource "null_resource" "create_vector_index" {
  triggers = {
    collection_id = aws_opensearchserverless_collection.main.id
  }

  depends_on = [time_sleep.wait_collection_active]

  provisioner "local-exec" {
    command = "python3 ${path.module}/scripts/create_index.py"
    environment = {
      AOSS_ENDPOINT = aws_opensearchserverless_collection.main.collection_endpoint
      AWS_REGION    = var.aws_region
      INDEX_NAME    = local.index_name
    }
  }
}

# ──────────────────────────────────────────────
# Bedrock Knowledge Base
# ──────────────────────────────────────────────
resource "aws_bedrockagent_knowledge_base" "main" {
  name     = "${var.project}-kb"
  role_arn = aws_iam_role.bedrock_kb.arn

  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0"
    }
  }

  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"
    opensearch_serverless_configuration {
      collection_arn    = aws_opensearchserverless_collection.main.arn
      vector_index_name = local.index_name
      field_mapping {
        metadata_field = "AMAZON_BEDROCK_METADATA"
        text_field     = "AMAZON_BEDROCK_TEXT_CHUNK"
        vector_field   = "bedrock-knowledge-base-default-vector"
      }
    }
  }

  depends_on = [null_resource.create_vector_index]

  tags = { Name = "${var.project}-kb" }
}

# ──────────────────────────────────────────────
# Bedrock Data Source（S3）
# ──────────────────────────────────────────────
resource "aws_bedrockagent_data_source" "main" {
  knowledge_base_id = aws_bedrockagent_knowledge_base.main.id
  name              = "${var.project}-kb-s3-datasource"

  data_deletion_policy = "RETAIN"

  data_source_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn         = var.s3_bucket_arn
      inclusion_prefixes = ["documents/"]
    }
  }
}
