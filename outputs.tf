output "namespace" {
  description = "?????Namespace?"
  value       = kubernetes_namespace.sample_app.metadata[0].name
}

output "deployment_name" {
  description = "?????Deployment?"
  value       = kubernetes_deployment.sample_app.metadata[0].name
}

output "service_name" {
  description = "?????Service?"
  value       = kubernetes_service.sample_app.metadata[0].name
}

output "configmap_name" {
  description = "?????ConfigMap?"
  value       = kubernetes_config_map.app_config.metadata[0].name
}
