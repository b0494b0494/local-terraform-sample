output "namespace" {
  description = "Created Namespace name"
  value       = kubernetes_namespace.sample_app.metadata[0].name
}

output "deployment_name" {
  description = "Created Deployment name"
  value       = kubernetes_deployment.sample_app.metadata[0].name
}

output "service_name" {
  description = "Created Service name"
  value       = kubernetes_service.sample_app.metadata[0].name
}

output "configmap_name" {
  description = "Created ConfigMap name"
  value       = kubernetes_config_map.app_config.metadata[0].name
}

output "secret_name" {
  description = "Created Secret name"
  value       = kubernetes_secret.app_secret.metadata[0].name
}

output "ingress_host" {
  description = "Ingress host (if enabled)"
  value       = var.enable_ingress ? var.ingress_host : null
}

output "ingress_enabled" {
  description = "Whether Ingress is enabled"
  value       = var.enable_ingress
}

output "hpa_enabled" {
  description = "Whether HPA is enabled"
  value       = var.enable_hpa
}

output "hpa_name" {
  description = "HPA name (if enabled)"
  value       = var.enable_hpa ? kubernetes_horizontal_pod_autoscaler.sample_app[0].metadata[0].name : null
}
