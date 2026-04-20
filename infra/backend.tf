# ステートバックエンドの値は backend.hcl に記述し、terraform init -backend-config=backend.hcl で初期化する
# backend.hcl は .gitignore 対象
terraform {
  backend "s3" {}
}
