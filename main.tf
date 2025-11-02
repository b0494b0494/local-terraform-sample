terraform {
  required_version = ">= 1.0"
  
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

provider "kubernetes" {
  # ローカルのエミュレータ（Minikube、kind、k3dなど）を使用
  # ~/.kube/configのデフォルトコンテキストを使用
  # 特定のコンテキストを使用する場合は以下の行のコメントを外してください
  config_path = "~/.kube/config"
  # config_context = "minikube"  # Minikubeの場合
  # config_context = "kind-kind"  # kindの場合
  # config_context = "k3d-default"  # k3dの場合
}

# Namespace
resource "kubernetes_namespace" "sample_app" {
  metadata {
    name = var.app_name
  }
}

# ConfigMap（アプリケーション設定）
resource "kubernetes_config_map" "app_config" {
  metadata {
    name      = "${var.app_name}-config"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app     = var.app_name
      env     = var.environment
      version = var.app_version
    }
  }

  data = {
    APP_NAME    = var.app_name
    APP_VERSION = var.app_version
    LOG_LEVEL   = var.log_level
  }
}

# Deployment
resource "kubernetes_deployment" "sample_app" {
  metadata {
    name      = var.app_name
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app     = var.app_name
      env     = var.environment
      version = var.app_version
    }
  }

  spec {
    replicas = var.replica_count

    selector {
      match_labels = {
        app = var.app_name
      }
    }

    template {
      metadata {
        labels = {
          app     = var.app_name
          env     = var.environment
          version = var.app_version
        }
      }

      spec {
        # Persistent Volume Claim for storage (if enabled)
        dynamic "volume" {
          for_each = var.enable_persistent_storage ? [1] : []
          content {
            name = "app-storage"
            persistent_volume_claim {
              claim_name = kubernetes_persistent_volume_claim.app_storage[0].metadata[0].name
            }
          }
        }

        container {
          image = "sample-app:latest"
          name  = "sample-app"

          port {
            container_port = 8080
          }

          # Volume mount (if persistent storage is enabled)
          dynamic "volume_mount" {
            for_each = var.enable_persistent_storage ? [1] : []
            content {
              name       = "app-storage"
              mount_path = "/app/data"
            }
          }

          # ConfigMapから環境変数を読み込む
          env {
            name = "ENVIRONMENT"
            value = "kubernetes"
          }

          env {
            name = "APP_NAME"
            value_from {
              config_map_key_ref {
                name = kubernetes_config_map.app_config.metadata[0].name
                key  = "APP_NAME"
              }
            }
          }

          env {
            name = "APP_VERSION"
            value_from {
              config_map_key_ref {
                name = kubernetes_config_map.app_config.metadata[0].name
                key  = "APP_VERSION"
              }
            }
          }

          env {
            name = "LOG_LEVEL"
            value_from {
              config_map_key_ref {
                name = kubernetes_config_map.app_config.metadata[0].name
                key  = "LOG_LEVEL"
              }
            }
          }

          # Secretから機密情報を読み込む（例：API Key）
          env {
            name = "API_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.app_secret.metadata[0].name
                key  = "api_key"
              }
            }
          }

          # Liveness Probe（コンテナが生きているか確認）
          liveness_probe {
            http_get {
              path = "/health"
              port = 8080
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds        = 5
            failure_threshold      = 3
          }

          # Readiness Probe（トラフィックを受け付ける準備ができているか確認）
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

# Service
resource "kubernetes_service" "sample_app" {
  metadata {
    name      = "${var.app_name}-service"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
  }

  spec {
    selector = {
      app = var.app_name
    }

    port {
      port        = 80
      target_port = 8080
    }

    type = "LoadBalancer"
  }
}
