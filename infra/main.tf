module "iam" {
  source     = "./modules/iam"
  project    = var.project
  aws_region = var.aws_region
}

module "bedrock" {
  source        = "./modules/bedrock"
  project       = var.project
  aws_region    = var.aws_region
  s3_bucket_arn = module.s3.s3_bucket_arn
}
