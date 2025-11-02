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
    name = "sample-app"
  }
}

# ConfigMap（アプリケーション設定）
resource "kubernetes_config_map" "app_config" {
  metadata {
    name      = "app-config"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = "sample-app"
    }
  }

  data = {
    APP_NAME    = "sample-app"
    APP_VERSION = "1.0.0"
    LOG_LEVEL   = "INFO"
  }
}

# Deployment
resource "kubernetes_deployment" "sample_app" {
  metadata {
    name      = "sample-app"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = "sample-app"
    }
  }

  spec {
    replicas = 2

    selector {
      match_labels = {
        app = "sample-app"
      }
    }

    template {
      metadata {
        labels = {
          app = "sample-app"
        }
      }

      spec {
        container {
          image = "sample-app:latest"
          name  = "sample-app"

          port {
            container_port = 8080
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
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu    = "200m"
              memory = "256Mi"
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
    name      = "sample-app-service"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = "sample-app"
    }
  }

  spec {
    selector = {
      app = "sample-app"
    }

    port {
      port        = 80
      target_port = 8080
    }

    type = "LoadBalancer"
  }
}
