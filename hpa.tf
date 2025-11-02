# Horizontal Pod Autoscaler (HPA)
# Automatically scales pods based on CPU and memory usage
# Enable with: terraform apply (enabled by default)

resource "kubernetes_horizontal_pod_autoscaler" "sample_app" {
  count = var.enable_hpa ? 1 : 0
  metadata {
    name      = "${var.app_name}-hpa"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
  }

  spec {
    min_replicas = var.hpa_min_replicas
    max_replicas = var.hpa_max_replicas

    target_cpu_utilization_percentage = var.hpa_target_cpu

    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment.sample_app.metadata[0].name
    }

    # Behavior configuration (Kubernetes 1.18+)
    # Controls how fast/slow scaling happens
    behavior {
      scale_down {
        stabilization_window_seconds = 300  # Wait 5 min before scaling down
        policies {
          type          = "Percent"
          value         = 50
          period_seconds = 60
        }
      }
      scale_up {
        stabilization_window_seconds = 0    # Scale up immediately
        policies {
          type          = "Percent"
          value         = 100
          period_seconds = 15
        }
        policies {
          type          = "Pods"
          value         = 2
          period_seconds = 60
        }
        select_policy = "Max"  # Use the policy that scales the most
      }
    }
  }
}
