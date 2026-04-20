# special = false にして URL エンコーディング問題を回避する
resource "random_password" "db" {
  length  = 32
  special = false
}

module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.12"

  identifier = "${var.project}-postgres"

  engine               = "postgres"
  engine_version       = "16.6"
  instance_class       = "db.t3.micro"
  allocated_storage    = 20
  storage_type         = "gp2"

  db_name  = "doc_drill"
  username = "docdrill"
  # RDS native Secrets Manager ではなく自前の random_password を使う
  # （DATABASE_URL 形式で Secrets Manager に格納するため）
  manage_master_user_password = false
  password                    = random_password.db.result

  # VPC モジュールが database_subnets 指定時にサブネットグループを自動作成する
  create_db_subnet_group = false
  db_subnet_group_name   = module.vpc.database_subnet_group_name
  vpc_security_group_ids = [aws_security_group.db.id]

  # パラメータグループ・オプショングループは不要
  create_db_parameter_group = false
  create_db_option_group    = false

  # フリーティア / 開発用設定
  publicly_accessible = false
  multi_az            = false
  skip_final_snapshot = true
  deletion_protection = false
  apply_immediately   = true
}

# ──────────────────────────────────────────────
# Secrets Manager: DATABASE_URL を格納
# ──────────────────────────────────────────────
resource "aws_secretsmanager_secret" "db" {
  name = "${var.project}/db-password"

  # 開発用: destroy 後に即時削除し、同名で再作成できるようにする
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id     = aws_secretsmanager_secret.db.id
  secret_string = "postgresql://docdrill:${random_password.db.result}@${module.rds.db_instance_address}:5432/doc_drill"
}
