# Kubernetes Secret for sensitive data
# In production, use external secret management (e.g., Vault, AWS Secrets Manager)

resource "kubernetes_secret" "app_secret" {
  metadata {
    name      = "app-secret"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = "sample-app"
    }
  }

  # Note: In production, never hardcode secrets!
  # Use data sources or external secret management
  data = {
    # Example: API key (base64 encoded)
    api_key = base64encode("example-api-key-12345")  # ?? Demo only!
    # Example: Database password
    db_password = base64encode("example-password")  # ?? Demo only!
  }

  type = "Opaque"
}
