output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "web_security_group_id" {
  description = "Web security group ID"
  value       = aws_security_group.web.id
}

output "app_security_group_id" {
  description = "App security group ID"
  value       = aws_security_group.app.id
}
