# Blue-Green Deployment Module
# Creates a deployment for either blue or green environment

resource "kubernetes_deployment" "app" {
  metadata {
    name      = "${var.app_name}-${var.environment}"
    namespace = var.namespace
    labels = merge({
      app         = var.app_name
      environment = var.environment
      version     = var.version
      deployment  = "blue-green"
    }, var.labels)
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app         = var.app_name
        environment = var.environment
      }
    }

    template {
      metadata {
        labels = merge({
          app         = var.app_name
          environment = var.environment
          version     = var.version
        }, var.labels)

        annotations = {
          "prometheus.io/scrape" = "true"
          "prometheus.io/port"   = "8080"
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        # ServiceAccount
        service_account_name = var.service_account_name != "" ? var.service_account_name : null

        container {
          name  = var.app_name
          image = var.image

          port {
            container_port = 8080
            name          = "http"
          }

          env {
            name = "APP_NAME"
            value_from {
              config_map_key_ref {
                name = var.config_map_name
                key  = "APP_NAME"
              }
            }
          }

          env {
            name = "APP_VERSION"
            value = var.version
          }

          env {
            name = "ENVIRONMENT"
            value = "${var.environment}-${var.version}"
          }

          env {
            name = "LOG_LEVEL"
            value_from {
              config_map_key_ref {
                name = var.config_map_name
                key  = "LOG_LEVEL"
              }
            }
          }

          # Health checks
          liveness_probe {
            http_get {
              path = "/health"
              port = 8080
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 3
          }

          readiness_probe {
            http_get {
              path = "/ready"
              port = 8080
            }
            initial_delay_seconds = 10
            period_seconds        = 5
            timeout_seconds       = 3
            failure_threshold     = 3
          }

          resources {
            requests = {
              cpu    = var.cpu_request
              memory = var.memory_request
            }
            limits = {
              cpu    = var.cpu_limit
              memory = var.memory_limit
            }
          }
        }
      }
    }
  }
}

# Service for blue/green environment (internal, for testing)
resource "kubernetes_service" "app" {
  metadata {
    name      = "${var.app_name}-${var.environment}"
    namespace = var.namespace
    labels = {
      app         = var.app_name
      environment = var.environment
      version     = var.version
    }
  }

  spec {
    selector = {
      app         = var.app_name
      environment = var.environment
    }

    port {
      port        = 8080
      target_port = 8080
      name        = "http"
    }

    type = "ClusterIP"
  }
}
