# Prometheus Monitoring Stack
# Provides professional-grade metrics collection and monitoring

# Namespace for monitoring stack
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = "monitoring"
    labels = {
      name = "monitoring"
    }
  }
}

# ServiceMonitor (for Prometheus to discover app metrics)
# Note: Requires Prometheus Operator to be installed
# For now, using manual scrape config approach
resource "kubernetes_config_map" "prometheus_config" {
  count = var.enable_prometheus ? 1 : 0

  metadata {
    name      = "prometheus-config"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "prometheus"
    }
  }

  data = {
    "prometheus.yml" = <<-EOF
      global:
        scrape_interval: 15s
        evaluation_interval: 15s

      scrape_configs:
        - job_name: 'sample-app'
          kubernetes_sd_configs:
            - role: pod
              namespaces:
                names:
                  - ${kubernetes_namespace.sample_app.metadata[0].name}
          relabel_configs:
            - source_labels: [__meta_kubernetes_pod_label_app]
              action: keep
              regex: ${var.app_name}
            - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
              action: keep
              regex: true
            - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
              action: replace
              target_label: __metrics_path__
              regex: (.+)
            - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
              action: replace
              regex: ([^:]+)(?::\d+)?;(\d+)
              replacement: $1:$2
              target_label: __address__
            - action: labelmap
              regex: __meta_kubernetes_pod_label_(.+)
            - source_labels: [__meta_kubernetes_namespace]
              action: replace
              target_label: kubernetes_namespace
            - source_labels: [__meta_kubernetes_pod_name]
              action: replace
              target_label: kubernetes_pod_name

        - job_name: 'prometheus'
          static_configs:
            - targets: ['localhost:9090']
      EOF
  }
}

# Prometheus Deployment (simplified - for local practice)
resource "kubernetes_deployment" "prometheus" {
  count = var.enable_prometheus ? 1 : 0

  metadata {
    name      = "prometheus"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "prometheus"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "prometheus"
      }
    }

    template {
      metadata {
        labels = {
          app = "prometheus"
        }
      }

      spec {
        container {
          image = "prom/prometheus:latest"
          name  = "prometheus"

          port {
            container_port = 9090
          }

          args = [
            "--config.file=/etc/prometheus/prometheus.yml",
            "--storage.tsdb.path=/prometheus",
            "--web.console.libraries=/etc/prometheus/console_libraries",
            "--web.console.templates=/etc/prometheus/consoles",
            "--storage.tsdb.retention.time=15d"
          ]

          volume_mount {
            name       = "prometheus-config"
            mount_path = "/etc/prometheus"
          }

          volume_mount {
            name       = "prometheus-storage"
            mount_path = "/prometheus"
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "1Gi"
            }
          }
        }

        volume {
          name = "prometheus-config"
          config_map {
            name = kubernetes_config_map.prometheus_config[0].metadata[0].name
          }
        }

        volume {
          name = "prometheus-storage"
          empty_dir {}
        }
      }
    }
  }
}

# Prometheus Service
resource "kubernetes_service" "prometheus" {
  count = var.enable_prometheus ? 1 : 0

  metadata {
    name      = "prometheus"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "prometheus"
    }
  }

  spec {
    selector = {
      app = "prometheus"
    }

    port {
      port        = 9090
      target_port = 9090
    }

    type = "ClusterIP"
  }
}

# Grafana Deployment
resource "kubernetes_deployment" "grafana" {
  count = var.enable_grafana ? 1 : 0

  metadata {
    name      = "grafana"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "grafana"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "grafana"
      }
    }

    template {
      metadata {
        labels = {
          app = "grafana"
        }
      }

      spec {
        container {
          image = "grafana/grafana:latest"
          name  = "grafana"

          port {
            container_port = 3000
          }

          env {
            name  = "GF_SECURITY_ADMIN_USER"
            value = "admin"
          }

          env {
            name  = "GF_SECURITY_ADMIN_PASSWORD"
            value = "admin"  # Change in production!
          }

          env {
            name  = "GF_SERVER_ROOT_URL"
            value = "%(protocol)s://%(domain)s:%(http_port)s/"
          }

          # Prometheus datasource configuration
          env {
            name  = "GF_INSTALL_PLUGINS"
            value = ""
          }

          volume_mount {
            name       = "grafana-storage"
            mount_path = "/var/lib/grafana"
          }

          volume_mount {
            name       = "grafana-datasource"
            mount_path = "/etc/grafana/provisioning/datasources"
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "256Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }
          }
        }

        volume {
          name = "grafana-storage"
          empty_dir {}
        }

        volume {
          name = "grafana-datasource"
          config_map {
            name = kubernetes_config_map.grafana_datasource[0].metadata[0].name
          }
        }
      }
    }
  }
}

# Grafana DataSource ConfigMap (Prometheus connection)
resource "kubernetes_config_map" "grafana_datasource" {
  count = var.enable_grafana ? 1 : 0

  metadata {
    name      = "grafana-datasource"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "grafana"
    }
  }

  data = {
    "prometheus.yaml" = <<-EOF
      apiVersion: 1
      datasources:
        - name: Prometheus
          type: prometheus
          access: proxy
          url: http://prometheus:9090
          isDefault: true
          editable: true
      EOF
  }
}

# Grafana Service
resource "kubernetes_service" "grafana" {
  count = var.enable_grafana ? 1 : 0

  metadata {
    name      = "grafana"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "grafana"
    }
  }

  spec {
    selector = {
      app = "grafana"
    }

    port {
      port        = 3000
      target_port = 3000
    }

    type = "ClusterIP"
  }
}
