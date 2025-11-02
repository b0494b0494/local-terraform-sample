# Blue-Green Deployment Module Outputs

output "deployment_name" {
  description = "Name of the deployment"
  value       = kubernetes_deployment.app.metadata[0].name
}

output "service_name" {
  description = "Name of the service"
  value       = kubernetes_service.app.metadata[0].name
}

output "environment" {
  description = "Environment (blue or green)"
  value       = var.environment
}

output "version" {
  description = "Application version"
  value       = var.version
}

output "selector_labels" {
  description = "Labels for service selector"
  value = {
    app         = var.app_name
    environment = var.environment
  }
}
