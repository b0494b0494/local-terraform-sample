# PostgreSQL Database
# Task 1.1: Database Integration
# Provides a PostgreSQL database for the application

resource "kubernetes_deployment" "postgresql" {
  count = var.enable_database ? 1 : 0

  metadata {
    name      = "${var.app_name}-postgresql"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app     = "${var.app_name}-postgresql"
      env     = var.environment
      service = "database"
    }
  }

  spec {
    replicas = 1  # Database is typically single instance

    selector {
      match_labels = {
        app = "${var.app_name}-postgresql"
      }
    }

    template {
      metadata {
        labels = {
          app = "${var.app_name}-postgresql"
          env = var.environment
        }
      }

      spec {
        container {
          name  = "postgresql"
          image = "postgres:16-alpine"

          port {
            container_port = 5432
            name          = "postgresql"
          }

          env {
            name  = "POSTGRES_DB"
            value = var.database_name
          }

          env {
            name  = "POSTGRES_USER"
            value = var.database_user
          }

          env {
            name = "POSTGRES_PASSWORD"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.database_credentials[0].metadata[0].name
                key  = "password"
              }
            }
          }

          env {
            name  = "PGDATA"
            value = "/var/lib/postgresql/data/pgdata"
          }

          resources {
            requests = {
              cpu    = "200m"
              memory = "256Mi"
            }
            limits = {
              cpu    = "1000m"
              memory = "512Mi"
            }
          }

          volume_mount {
            name       = "postgresql-data"
            mount_path = "/var/lib/postgresql/data"
          }

          liveness_probe {
            exec {
              command = ["pg_isready", "-U", var.database_user]
            }
            initial_delay_seconds = 30
            period_seconds        = 10
            timeout_seconds       = 5
            failure_threshold     = 3
          }

          readiness_probe {
            exec {
              command = ["pg_isready", "-U", var.database_user]
            }
            initial_delay_seconds = 10
            period_seconds        = 5
            timeout_seconds       = 3
            failure_threshold     = 3
          }
        }

        volume {
          name = "postgresql-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.postgresql_data[0].metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "postgresql" {
  count = var.enable_database ? 1 : 0

  metadata {
    name      = "${var.app_name}-postgresql"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = "${var.app_name}-postgresql"
      env = var.environment
    }
  }

  spec {
    type = "ClusterIP"
    selector = {
      app = "${var.app_name}-postgresql"
    }

    port {
      port        = 5432
      target_port = 5432
      protocol    = "TCP"
      name        = "postgresql"
    }
  }
}

# Persistent Volume Claim for PostgreSQL data
resource "kubernetes_persistent_volume_claim" "postgresql_data" {
  count = var.enable_database ? 1 : 0

  metadata {
    name      = "${var.app_name}-postgresql-data"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = "${var.app_name}-postgresql"
      env = var.environment
    }
  }

  spec {
    access_modes = ["ReadWriteOnce"]

    resources {
      requests = {
        storage = var.database_storage_size
      }
    }

    storage_class_name = kubernetes_storage_class.local_storage.metadata[0].name
  }
}

# Secret for database credentials
resource "kubernetes_secret" "database_credentials" {
  count = var.enable_database ? 1 : 0

  metadata {
    name      = "${var.app_name}-db-credentials"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
  }

  data = {
    username = base64encode(var.database_user)
    password = base64encode(var.database_password)
    database = base64encode(var.database_name)
  }

  type = "Opaque"
}
