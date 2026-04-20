# database
output "db_endpoint" {
  value = module.rds.db_instance_address
}

output "db_secret_arn" {
  value = aws_secretsmanager_secret.db.arn
}

# s3
output "s3_bucket_name" {
  value = module.s3.s3_bucket_id
}

output "s3_bucket_arn" {
  value = module.s3.s3_bucket_arn
}

# iam
output "task_execution_role_arn" {
  value = module.iam.task_execution_role_arn
}

output "backend_task_role_arn" {
  value = module.iam.backend_task_role_arn
}

# networking
output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnet_ids" {
  value = module.vpc.public_subnets
}

output "private_subnet_ids" {
  value = module.vpc.private_subnets
}

output "db_subnet_ids" {
  value = module.vpc.database_subnets
}

output "frontend_alb_sg_id" {
  value = aws_security_group.frontend_alb.id
}

output "backend_alb_sg_id" {
  value = aws_security_group.backend_alb.id
}

output "frontend_ecs_sg_id" {
  value = aws_security_group.frontend_ecs.id
}

output "backend_ecs_sg_id" {
  value = aws_security_group.backend_ecs.id
}

output "db_sg_id" {
  value = aws_security_group.db.id
}

# ecr
output "frontend_repository_url" {
  value = module.ecr_frontend.repository_url
}

output "backend_repository_url" {
  value = module.ecr_backend.repository_url
}

# alb
output "frontend_alb_dns" {
  value = module.alb_frontend.dns_name
}

output "backend_alb_dns" {
  value = module.alb_backend.dns_name
}

# bedrock
output "bedrock_kb_id" {
  value = module.bedrock.knowledge_base_id
}

output "bedrock_data_source_id" {
  value = module.bedrock.data_source_id
}

# ecs
output "ecs_cluster_arn" {
  value = module.ecs_cluster.cluster_arn
}
