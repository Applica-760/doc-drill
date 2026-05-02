module "iam" {
  source     = "./modules/iam"
  project    = var.project
  aws_region = var.aws_region
}

