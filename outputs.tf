output "namespace" {
  description = "Created Namespace name"
  value       = kubernetes_namespace.sample_app.metadata[0].name
}

output "deployment_name" {
  description = "Created Deployment name"
  value       = var.enable_blue_green ? (var.active_environment == "blue" ? module.blue_deployment[0].deployment_name : module.green_deployment[0].deployment_name) : kubernetes_deployment.sample_app[0].metadata[0].name
}

output "service_name" {
  description = "Created Service name"
  value       = var.enable_blue_green ? (kubernetes_service.app_main[0].metadata[0].name) : kubernetes_service.sample_app[0].metadata[0].name
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

output "storage_enabled" {
  description = "Whether persistent storage is enabled"
  value       = var.enable_persistent_storage
}

output "pvc_name" {
  description = "PVC name (if storage enabled)"
  value       = var.enable_persistent_storage ? kubernetes_persistent_volume_claim.app_storage[0].metadata[0].name : null
}

output "service_account_name" {
  description = "ServiceAccount name"
  value       = kubernetes_service_account.app_sa.metadata[0].name
}

output "role_name" {
  description = "Role name"
  value       = kubernetes_role.app_role.metadata[0].name
}

output "prometheus_enabled" {
  description = "Whether Prometheus is enabled"
  value       = var.enable_prometheus
}

output "prometheus_service" {
  description = "Prometheus service name (if enabled)"
  value       = var.enable_prometheus ? kubernetes_service.prometheus[0].metadata[0].name : null
}

output "prometheus_namespace" {
  description = "Prometheus namespace"
  value       = var.enable_prometheus ? kubernetes_namespace.monitoring.metadata[0].name : null
}

output "grafana_enabled" {
  description = "Whether Grafana is enabled"
  value       = var.enable_grafana
}

output "grafana_service" {
  description = "Grafana service name (if enabled)"
  value       = var.enable_grafana ? kubernetes_service.grafana[0].metadata[0].name : null
}

output "loki_enabled" {
  description = "Whether Loki is enabled"
  value       = var.enable_loki
}

output "loki_service" {
  description = "Loki service name (if enabled)"
  value       = var.enable_loki ? kubernetes_service.loki[0].metadata[0].name : null
}

output "network_policies_enabled" {
  description = "Whether Network Policies are enabled"
  value       = var.enable_network_policies
}

output "redis_enabled" {
  description = "Whether Redis cache is enabled"
  value       = var.enable_redis
}
