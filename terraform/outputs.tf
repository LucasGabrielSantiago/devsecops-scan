output "ecr_repository_url" {
  description = "URL do repositório ECR para o docker push"
  value       = aws_ecr_repository.app.repository_url
}

output "service_url" {
  description = "URL pública da API no App Runner"
  value       = "https://${aws_apprunner_service.app.service_url}"
}
