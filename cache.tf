# Redis Cache Layer
# Task 1.2: Cache Layer with Redis

resource "kubernetes_deployment" "redis" {
  count = var.enable_redis ? 1 : 0
  metadata {
    name      = "${var.app_name}-redis"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app     = "${var.app_name}-redis"
      env     = var.environment
      service = "cache"
    }
  }

  spec {
    replicas = 1  # Redis is typically single instance for cache

    selector {
      match_labels = {
        app = "${var.app_name}-redis"
      }
    }

    template {
      metadata {
        labels = {
          app = "${var.app_name}-redis"
          env = var.environment
        }
      }

      spec {
        container {
          name  = "redis"
          image = "redis:7-alpine"

          port {
            container_port = 6379
            name          = "redis"
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "256Mi"
            }
          }

          volume_mount {
            name       = "redis-data"
            mount_path = "/data"
          }

          command = ["redis-server"]
          args    = ["--appendonly", "yes"]
        }

        volume {
          name = "redis-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.redis_data[0].metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "redis" {
  count = var.enable_redis ? 1 : 0
  
  metadata {
    name      = "${var.app_name}-redis"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = "${var.app_name}-redis"
      env = var.environment
    }
  }

  spec {
    type = "ClusterIP"
    selector = {
      app = "${var.app_name}-redis"
    }

    port {
      port        = 6379
      target_port = 6379
      protocol    = "TCP"
      name        = "redis"
    }
  }
}

# Persistent Volume Claim for Redis data
resource "kubernetes_persistent_volume_claim" "redis_data" {
  count = var.enable_redis ? 1 : 0
  
  metadata {
    name      = "${var.app_name}-redis-data"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = "${var.app_name}-redis"
      env = var.environment
    }
  }

  spec {
    access_modes = ["ReadWriteOnce"]

    resources {
      requests = {
        storage = var.redis_storage_size
      }
    }

    storage_class_name = var.enable_persistent_storage ? kubernetes_storage_class.local_storage[0].metadata[0].name : null
  }
}
