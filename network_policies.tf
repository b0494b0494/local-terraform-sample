# Network Policies
# Task 1.3: Network Policies for pod-to-pod communication control
# 
# Network Policies enforce network isolation and allow fine-grained control
# over which pods can communicate with each other.

# Default deny-all policy for sample-app namespace
# This ensures that pods in this namespace can only communicate
# with explicitly allowed pods/services
resource "kubernetes_network_policy" "default_deny_all" {
  count = var.enable_network_policies ? 1 : 0

  metadata {
    name      = "${var.app_name}-default-deny"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
  }

  spec {
    pod_selector {
      match_labels = {}
    }

    policy_types = ["Ingress", "Egress"]

    # No ingress or egress rules means deny all
    # Specific rules will be added by other policies
  }
}

# Allow app pods to communicate with Redis
resource "kubernetes_network_policy" "allow_app_to_redis" {
  count = var.enable_network_policies && var.enable_redis ? 1 : 0

  metadata {
    name      = "${var.app_name}-allow-to-redis"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
  }

  spec {
    pod_selector {
      match_labels = {
        app = var.app_name
      }
    }

    policy_types = ["Egress"]

    egress {
      # Allow egress to Redis service
      to {
        pod_selector {
          match_labels = {
            app = "${var.app_name}-redis"
          }
        }
      }
      ports {
        port     = "6379"
        protocol = "TCP"
      }
    }
  }
}

# Allow app pods to receive traffic from Service (ClusterIP)
# This allows the Kubernetes Service to route traffic to pods
resource "kubernetes_network_policy" "allow_service_to_app" {
  count = var.enable_network_policies ? 1 : 0

  metadata {
    name      = "${var.app_name}-allow-from-service"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
  }

  spec {
    pod_selector {
      match_labels = {
        app = var.app_name
      }
    }

    policy_types = ["Ingress"]

    ingress {
      # Allow ingress from any pod in the same namespace
      # (typically via Service)
      from {
        namespace_selector {
          match_labels = {
            name = kubernetes_namespace.sample_app.metadata[0].name
          }
        }
      }
      ports {
        port     = "8080"
        protocol = "TCP"
      }
    }

    # Also allow ingress from monitoring namespace (if Prometheus is enabled)
    dynamic "ingress" {
      for_each = var.enable_prometheus ? [1] : []
      content {
        from {
          namespace_selector {
            match_labels = {
              name = "monitoring"
            }
          }
        }
        ports {
          port     = "8080"
          protocol = "TCP"
        }
      }
    }
  }
}

# Allow app pods to make DNS queries (required for Service discovery)
resource "kubernetes_network_policy" "allow_dns" {
  count = var.enable_network_policies ? 1 : 0

  metadata {
    name      = "${var.app_name}-allow-dns"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
  }

  spec {
    pod_selector {
      match_labels = {
        app = var.app_name
      }
    }

    policy_types = ["Egress"]

    egress {
      # Allow DNS queries to kube-dns
      to {
        namespace_selector {
          match_labels = {
            name = "kube-system"
          }
        }
        pod_selector {
          match_labels = {
            k8s-app = "kube-dns"
          }
        }
      }
      ports {
        port     = "53"
        protocol = "UDP"
      }
      ports {
        port     = "53"
        protocol = "TCP"
      }
    }

    # Also allow DNS for Redis pods
    dynamic "egress" {
      for_each = var.enable_redis ? [1] : []
      content {
        to {
          namespace_selector {
            match_labels = {
              name = "kube-system"
            }
          }
          pod_selector {
            match_labels = {
              k8s-app = "kube-dns"
            }
          }
        }
        ports {
          port     = "53"
          protocol = "UDP"
        }
        ports {
          port     = "53"
          protocol = "TCP"
        }
      }
    }
  }
}

# Allow monitoring namespace to scrape metrics from app pods
resource "kubernetes_network_policy" "allow_monitoring_scrape" {
  count = var.enable_network_policies && var.enable_prometheus ? 1 : 0

  metadata {
    name      = "${var.app_name}-allow-monitoring-scrape"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
  }

  spec {
    pod_selector {
      match_labels = {
        app = var.app_name
      }
    }

    policy_types = ["Ingress"]

    ingress {
      # Allow Prometheus from monitoring namespace
      from {
        namespace_selector {
          match_labels = {
            name = "monitoring"
          }
        }
        pod_selector {
          match_labels = {
            app = "prometheus"
          }
        }
      }
      ports {
        port     = "8080"
        protocol = "TCP"
      }
    }
  }
}
