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
  # ????????????Minikube?kind?k3d??????
  # ~/.kube/config???????????????
  # ??????????????????????????????????
  config_path = "~/.kube/config"
  # config_context = "minikube"  # Minikube???
  # config_context = "kind-kind"  # kind???
  # config_context = "k3d-default"  # k3d???
}

# Namespace
resource "kubernetes_namespace" "sample_app" {
  metadata {
    name = "sample-app"
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

          env {
            name  = "ENVIRONMENT"
            value = "kubernetes"
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
