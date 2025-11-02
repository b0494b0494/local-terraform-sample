# Ingress for external access
# Enable with: terraform apply -var="enable_ingress=true"

resource "kubernetes_ingress" "sample_app" {
  count = var.enable_ingress ? 1 : 0

  metadata {
    name      = "${var.app_name}-ingress"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
    annotations = {
      "kubernetes.io/ingress.class"                = "nginx"
      "nginx.ingress.kubernetes.io/rewrite-target" = "/"
      # SSL/TLS (when certificates are available)
      # "cert-manager.io/cluster-issuer" = "letsencrypt-prod"
    }
  }

  spec {
    rule {
      host = var.ingress_host

      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = kubernetes_service.sample_app.metadata[0].name
              port {
                number = 80
              }
            }
          }
        }
      }
    }

    # TLS configuration (when certificates are available)
    # tls {
    #   hosts       = [var.ingress_host]
    #   secret_name = "${var.app_name}-tls"
    # }
  }
}
