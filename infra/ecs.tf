# cluster_settings のデフォルトが containerInsights=enabled のため上書き不要
module "ecs_cluster" {
  source  = "terraform-aws-modules/ecs/aws"
  version = "~> 5.12"

  cluster_name = var.project
}

# ──────────────────────────────────────────────
# CloudWatch Log Groups
# ──────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project}/backend"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "frontend" {
  name              = "/ecs/${var.project}/frontend"
  retention_in_days = 7
}

# ──────────────────────────────────────────────
# Task Definitions
# ──────────────────────────────────────────────
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = module.iam.task_execution_role_arn
  task_role_arn            = module.iam.backend_task_role_arn

  container_definitions = jsonencode([{
    name  = "backend"
    image = "${module.ecr_backend.repository_url}:latest"
    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]
    secrets = [{
      name      = "DATABASE_URL"
      valueFrom = aws_secretsmanager_secret.db.arn
    }]
    environment = [
      { name = "S3_BUCKET",                 value = module.s3.s3_bucket_id },
      { name = "AWS_DEFAULT_REGION",        value = var.aws_region },
      { name = "BEDROCK_KB_ENABLED",        value = "true" },
      { name = "BEDROCK_KB_ID",             value = module.bedrock.knowledge_base_id },
      { name = "BEDROCK_KB_DATA_SOURCE_ID", value = module.bedrock.data_source_id },
      { name = "CORS_ORIGINS",              value = "[\"http://${module.alb_frontend.dns_name}\"]" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.backend.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# NEXT_PUBLIC_* はビルド時に埋め込まれるため、クライアントサイド fetch には
# docker build --build-arg NEXT_PUBLIC_API_URL=http://{backend_alb_dns} が必要。
# ここでの設定はサーバーサイドレンダリング用途にのみ有効。
resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.project}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = module.iam.task_execution_role_arn

  container_definitions = jsonencode([{
    name  = "frontend"
    image = "${module.ecr_frontend.repository_url}:latest"
    portMappings = [{
      containerPort = 3000
      protocol      = "tcp"
    }]
    environment = [
      { name = "HOSTNAME",            value = "0.0.0.0" },
      { name = "NEXT_PUBLIC_API_URL", value = "http://${module.alb_backend.dns_name}" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# ──────────────────────────────────────────────
# ECS Services
# lifecycle.ignore_changes は meta-argument のためモジュール経由で渡せない
# → CI/CD（GitHub Actions）がタスク定義を更新しても Terraform が上書きしない
# ──────────────────────────────────────────────
resource "aws_ecs_service" "backend" {
  name            = "${var.project}-backend"
  cluster         = module.ecs_cluster.cluster_arn
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.backend_ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = module.alb_backend.target_groups["default"].arn
    container_name   = "backend"
    container_port   = 8000
  }

  health_check_grace_period_seconds = 30

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }
}

resource "aws_ecs_service" "frontend" {
  name            = "${var.project}-frontend"
  cluster         = module.ecs_cluster.cluster_arn
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.frontend_ecs.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = module.alb_frontend.target_groups["default"].arn
    container_name   = "frontend"
    container_port   = 3000
  }

  health_check_grace_period_seconds = 60

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }
}
