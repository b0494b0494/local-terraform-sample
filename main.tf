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
# Standard deployment (used when blue-green is disabled)
resource "kubernetes_deployment" "sample_app" {
  count = var.enable_blue_green ? 0 : 1
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
        annotations = {
          # Prometheus scraping annotations
          "prometheus.io/scrape" = var.enable_prometheus ? "true" : "false"
          "prometheus.io/port"   = "8080"
          "prometheus.io/path"   = "/metrics"
        }
      }

      spec {
        # ServiceAccount for RBAC
        service_account_name = kubernetes_service_account.app_sa.metadata[0].name

        # Init Containers
        # These run before the main containers start
        dynamic "init_container" {
          for_each = var.enable_redis ? [1] : []
          content {
            name  = "wait-for-redis"
            image = "busybox:1.36"

            command = [
              "sh",
              "-c",
              <<-EOT
                echo "Waiting for Redis to be ready..."
                until nc -z ${var.app_name}-redis 6379; do
                  echo "Redis not ready, waiting..."
                  sleep 2
                done
                echo "Redis is ready!"
              EOT
            ]
          }
        }

        dynamic "init_container" {
          for_each = var.enable_database ? [1] : []
          content {
            name  = "wait-for-database"
            image = "busybox:1.36"

            command = [
              "sh",
              "-c",
              <<-EOT
                echo "Waiting for PostgreSQL to be ready..."
                until nc -z ${var.app_name}-postgresql 5432; do
                  echo "Database not ready, waiting..."
                  sleep 2
                done
                echo "Database is ready!"
              EOT
            ]
          }
        }

        dynamic "init_container" {
          for_each = var.enable_database ? [1] : []
          content {
            name  = "migrate-database"
            image = "sample-app:latest"

            command = ["python", "migration.py"]

            env {
              name = "DATABASE_HOST"
              value = "${var.app_name}-postgresql"
            }

            env {
              name = "DATABASE_PORT"
              value = "5432"
            }

            env {
              name = "DATABASE_NAME"
              value_from {
                secret_key_ref {
                  name = kubernetes_secret.database_credentials[0].metadata[0].name
                  key  = "database"
                }
              }
            }

            env {
              name = "DATABASE_USER"
              value_from {
                secret_key_ref {
                  name = kubernetes_secret.database_credentials[0].metadata[0].name
                  key  = "username"
                }
              }
            }

            env {
              name = "DATABASE_PASSWORD"
              value_from {
                secret_key_ref {
                  name = kubernetes_secret.database_credentials[0].metadata[0].name
                  key  = "password"
                }
              }
            }
          }
        }

        dynamic "init_container" {
          for_each = [1]  # Always run config validation
          content {
            name  = "validate-config"
            image = "busybox:1.36"

            command = [
              "sh",
              "-c",
              <<-EOT
                echo "Validating configuration..."
                # Check required environment variables are set
                if [ -z "$APP_NAME" ] || [ -z "$APP_VERSION" ]; then
                  echo "ERROR: Required environment variables not set"
                  exit 1
                fi
                echo "Configuration validated successfully"
              EOT
            ]

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
          }
        }

        # Init containers run in order:
        # 1. wait-for-redis (if Redis enabled)
        # 2. wait-for-database (if Database enabled)
        # 3. validate-config (always)
        # 4. migrate-database (if Database enabled)
        # 5. Main container starts

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

          # Redis connection (if enabled)
          dynamic "env" {
            for_each = var.enable_redis ? [1] : []
            content {
              name  = "REDIS_HOST"
              value = "${var.app_name}-redis"
            }
          }

          dynamic "env" {
            for_each = var.enable_redis ? [1] : []
            content {
              name  = "REDIS_PORT"
              value = "6379"
            }
          }

          # Database connection (if enabled)
          dynamic "env" {
            for_each = var.enable_database ? [1] : []
            content {
              name  = "DATABASE_HOST"
              value = "${var.app_name}-postgresql"
            }
          }

          dynamic "env" {
            for_each = var.enable_database ? [1] : []
            content {
              name  = "DATABASE_PORT"
              value = "5432"
            }
          }

          dynamic "env" {
            for_each = var.enable_database ? [1] : []
            content {
              name = "DATABASE_NAME"
              value_from {
                secret_key_ref {
                  name = kubernetes_secret.database_credentials[0].metadata[0].name
                  key  = "database"
                }
              }
            }
          }

          dynamic "env" {
            for_each = var.enable_database ? [1] : []
            content {
              name = "DATABASE_USER"
              value_from {
                secret_key_ref {
                  name = kubernetes_secret.database_credentials[0].metadata[0].name
                  key  = "username"
                }
              }
            }
          }

          dynamic "env" {
            for_each = var.enable_database ? [1] : []
            content {
              name = "DATABASE_PASSWORD"
              value_from {
                secret_key_ref {
                  name = kubernetes_secret.database_credentials[0].metadata[0].name
                  key  = "password"
                }
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

          # Mount shared log volume
          dynamic "volume_mount" {
            for_each = var.enable_sidecar_log_shipper ? [1] : []
            content {
              name       = "shared-logs"
              mount_path = "/app/logs"
            }
          }
        }

        # Sidecar Container: Log Shipper
        # Reads logs from shared volume and processes them
        dynamic "container" {
          for_each = var.enable_sidecar_log_shipper ? [1] : []
          content {
            name  = "log-shipper"
            image = "busybox:1.36"

            command = [
              "sh",
              "-c",
              <<-EOT
                echo "Log shipper sidecar started..."
                echo "Monitoring log files in /shared/logs..."
                
                # Simulate log shipping
                while true; do
                  if [ -f /shared/logs/app.log ]; then
                    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] Processing logs..."
                    # In production, this would ship to Loki, ELK, etc.
                    tail -n 10 /shared/logs/app.log 2>/dev/null || echo "No logs yet..."
                    sleep 30
                  else
                    echo "Waiting for log file..."
                    sleep 5
                  fi
                done
              EOT
            ]

            resources {
              requests = {
                cpu    = "50m"
                memory = "64Mi"
              }
              limits = {
                cpu    = "200m"
                memory = "128Mi"
              }
            }

            volume_mount {
              name       = "shared-logs"
              mount_path = "/shared/logs"
            }
          }
        }

        # Sidecar Container: Metrics Exporter
        # Exports additional metrics from the application
        dynamic "container" {
          for_each = var.enable_sidecar_metrics ? [1] : []
          content {
            name  = "metrics-exporter"
            image = "busybox:1.36"

            command = [
              "sh",
              "-c",
              <<-EOT
                echo "Metrics exporter sidecar started..."
                echo "Collecting metrics from shared volume..."
                
                # Simulate metrics export
                while true; do
                  echo "[$(date +%Y-%m-%d\ %H:%M:%S)] Metrics collection cycle"
                  # In production, this would export to Prometheus, etc.
                  sleep 60
                done
              EOT
            ]

            resources {
              requests = {
                cpu    = "50m"
                memory = "64Mi"
              }
              limits = {
                cpu    = "200m"
                memory = "128Mi"
              }
            }

            volume_mount {
              name       = "shared-logs"
              mount_path = "/shared/metrics"
            }
          }
        }

        # Shared volumes for sidecar containers
        dynamic "volume" {
          for_each = var.enable_sidecar_log_shipper || var.enable_sidecar_metrics ? [1] : []
          content {
            name = "shared-logs"
            empty_dir {
              medium = "Memory"
              size_limit = "100Mi"
            }
          }
        }
      }
    }
  }
}

# Service
# Standard service (used when blue-green is disabled)
resource "kubernetes_service" "sample_app" {
  count = var.enable_blue_green ? 0 : 1
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
