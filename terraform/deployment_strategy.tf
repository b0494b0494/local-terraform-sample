# Blue-Green Deployment Strategy
# Enables zero-downtime deployments with blue/green environments
# Variables are defined in variables.tf

# Blue environment deployment
module "blue_deployment" {
  count = var.enable_blue_green ? 1 : 0

  source = "./modules/blue-green"

  app_name    = var.app_name
  namespace   = kubernetes_namespace.sample_app.metadata[0].name
  image       = "${var.app_name}:${var.app_image_tag}"
  replicas    = var.replica_count
  environment = "blue"
  version     = var.app_version

  cpu_request    = var.cpu_request
  memory_request = var.memory_request
  cpu_limit      = var.cpu_limit
  memory_limit   = var.memory_limit

  config_map_name     = kubernetes_config_map.app_config.metadata[0].name
  service_account_name = var.enable_rbac ? kubernetes_service_account.app_sa.metadata[0].name : ""

  labels = {
    env     = var.environment
    version = var.app_version
  }
}

# Green environment deployment
module "green_deployment" {
  count = var.enable_blue_green ? 1 : 0

  source = "./modules/blue-green"

  app_name    = var.app_name
  namespace   = kubernetes_namespace.sample_app.metadata[0].name
  image       = "${var.app_name}:${var.app_image_tag}"
  replicas    = var.replica_count
  environment = "green"
  version     = var.app_version

  cpu_request    = var.cpu_request
  memory_request = var.memory_request
  cpu_limit      = var.cpu_limit
  memory_limit   = var.memory_limit

  config_map_name     = kubernetes_config_map.app_config.metadata[0].name
  service_account_name = var.enable_rbac ? kubernetes_service_account.app_sa.metadata[0].name : ""

  labels = {
    env     = var.environment
    version = var.app_version
  }
}

# Main service that routes traffic to active environment
resource "kubernetes_service" "app_main" {
  count = var.enable_blue_green ? 1 : 0

  metadata {
    name      = "${var.app_name}-main"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app         = var.app_name
      environment = "main"
    }
  }

  spec {
    # Selector switches based on active_environment
    selector = var.active_environment == "blue" ? module.blue_deployment[0].selector_labels : module.green_deployment[0].selector_labels

    port {
      port        = 8080
      target_port = 8080
      name        = "http"
    }

    type = "ClusterIP"
  }

  lifecycle {
    ignore_changes = [
      spec[0].selector
    ]
  }
}

# Local value to help with switching
locals {
  active_deployment = var.active_environment == "blue" ? module.blue_deployment[0].deployment_name : module.green_deployment[0].deployment_name
  inactive_deployment = var.active_environment == "blue" ? module.green_deployment[0].deployment_name : module.blue_deployment[0].deployment_name
}
