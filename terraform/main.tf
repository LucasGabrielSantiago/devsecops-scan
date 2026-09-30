###############################################################################
# Infraestrutura da API de Tarefas na AWS
#
#   ECR (registro da imagem Docker)  ->  App Runner (execução do container)
#
# O código é analisado pelo Checkov na pipeline (IaC security scan).
# Provisionar de fato é opcional:  terraform init && terraform apply
###############################################################################

data "aws_caller_identity" "current" {}

# --------------------------------------------------------------------------- #
# KMS: chave gerenciada pelo cliente para criptografar o repositório ECR
# --------------------------------------------------------------------------- #
resource "aws_kms_key" "ecr" {
  description             = "Criptografia do repositorio ECR ${var.app_name}"
  enable_key_rotation     = true
  deletion_window_in_days = 7

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PermiteAdministracaoPelaConta"
        Effect    = "Allow"
        Principal = { AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      }
    ]
  })
}

# --------------------------------------------------------------------------- #
# ECR: tags imutáveis, scan de vulnerabilidades no push e criptografia KMS
# --------------------------------------------------------------------------- #
resource "aws_ecr_repository" "app" {
  name                 = var.app_name
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "KMS"
    kms_key         = aws_kms_key.ecr.arn
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Mantem apenas as 10 imagens mais recentes"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

# --------------------------------------------------------------------------- #
# IAM: papel mínimo para o App Runner puxar a imagem do ECR
# --------------------------------------------------------------------------- #
resource "aws_iam_role" "apprunner_ecr_access" {
  name = "${var.app_name}-apprunner-ecr-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "build.apprunner.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr_access" {
  role       = aws_iam_role.apprunner_ecr_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# --------------------------------------------------------------------------- #
# App Runner: executa o container publicado no ECR
# --------------------------------------------------------------------------- #
resource "aws_apprunner_service" "app" {
  service_name = var.app_name

  source_configuration {
    auto_deployments_enabled = true

    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_ecr_access.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.app.repository_url}:${var.image_tag}"
      image_repository_type = "ECR"

      image_configuration {
        port = "8000"
      }
    }
  }

  health_check_configuration {
    protocol = "HTTP"
    path     = "/health"
  }

  instance_configuration {
    cpu    = "256"
    memory = "512"
  }

  depends_on = [aws_iam_role_policy_attachment.apprunner_ecr_access]
}
