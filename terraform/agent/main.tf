data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  account-id = data.aws_caller_identity.current.account_id
}

resource "aws_iam_role" "agent_runtime_role" {
  name = "${var.agent_runtime_name}-agent-runtime-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock-agentcore.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = "${local.account-id}"
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:bedrock-agentcore:${data.aws_region.current.region}:${local.account-id}:*"
          }
        }
      }
    ]
  })
}


resource "aws_iam_role_policy" "agent_runtime_policy" {
  role = aws_iam_role.agent_runtime_role.name
  name = "${var.agent_runtime_name}-agent-runtime-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "ecr:GetAuthorizationToken",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "xray:PutTraceSegments",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets",
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}




resource "awscc_bedrockagentcore_runtime" "agent_runtime" {
  agent_runtime_name = var.agent_runtime_name
  description        = "Bedrock Agent Runtime for ${var.agent_runtime_name}"
  role_arn           = aws_iam_role.agent_runtime_role.arn

  agent_runtime_artifact = {
    container_configuration = {
      container_uri = var.container_uri
    }
  }

  network_configuration = {
    network_mode = "PUBLIC" # will be modified to use VPC constraints once available
  }
}
