variable "repository_name" {
  description = "Name of the repo"
  type        = string
}

variable "iam_role_name" {
  type        = string
  description = "Name of the IAM role used by GitHub Actions to push to ECR"
}

variable "aws_account_id" {
  description = "Target AWS Account ID"
  type        = string
}
