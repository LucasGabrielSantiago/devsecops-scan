variable "aws_region" {
  description = "Região AWS onde a infraestrutura será criada"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Nome base dos recursos"
  type        = string
  default     = "api-tarefas"
}

variable "image_tag" {
  description = "Tag da imagem Docker a ser implantada (ex.: SHA do commit)"
  type        = string
  default     = "latest"
}
