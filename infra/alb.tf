module "alb_frontend" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 9.12"

  name    = "${var.project}-frontend"
  vpc_id  = module.vpc.vpc_id
  subnets = module.vpc.public_subnets

  create_security_group      = false
  security_groups            = [aws_security_group.frontend_alb.id]
  enable_deletion_protection = false

  target_groups = {
    default = {
      name                 = "${var.project}-frontend-tg"
      protocol             = "HTTP"
      port                 = 3000
      target_type          = "ip"
      deregistration_delay = 30
      create_attachment    = false
      health_check = {
        path                = "/"
        healthy_threshold   = 2
        unhealthy_threshold = 3
        interval            = 30
        timeout             = 5
      }
    }
  }

  listeners = {
    http = {
      port     = 80
      protocol = "HTTP"
      forward  = { target_group_key = "default" }
    }
  }
}

module "alb_backend" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 9.12"

  name    = "${var.project}-backend"
  vpc_id  = module.vpc.vpc_id
  subnets = module.vpc.public_subnets

  create_security_group      = false
  security_groups            = [aws_security_group.backend_alb.id]
  enable_deletion_protection = false

  target_groups = {
    default = {
      name                 = "${var.project}-backend-tg"
      protocol             = "HTTP"
      port                 = 8000
      target_type          = "ip"
      deregistration_delay = 30
      create_attachment    = false
      health_check = {
        path                = "/health"
        healthy_threshold   = 2
        unhealthy_threshold = 3
        interval            = 30
        timeout             = 5
      }
    }
  }

  listeners = {
    http = {
      port     = 80
      protocol = "HTTP"
      forward  = { target_group_key = "default" }
    }
  }
}
