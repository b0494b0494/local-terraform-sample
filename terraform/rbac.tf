# ServiceAccount and RBAC (Role-Based Access Control)
# Provides fine-grained permissions for pods and users

# ServiceAccount for the application
resource "kubernetes_service_account" "app_sa" {
  metadata {
    name      = "${var.app_name}-sa"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
    annotations = {
      # Example: AWS IAM role annotation (for EKS)
      # "eks.amazonaws.com/role-arn" = "arn:aws:iam::ACCOUNT_ID:role/app-role"
    }
  }
}

# Role (namespace-scoped permissions)
resource "kubernetes_role" "app_role" {
  metadata {
    name      = "${var.app_name}-role"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
  }

  # Permissions for the application
  rule {
    api_groups = [""]
    resources  = ["configmaps", "secrets"]
    verbs      = ["get", "list"]
  }

  rule {
    api_groups = [""]
    resources  = ["pods"]
    verbs      = ["get", "list"]
  }

  # Example: Allow reading logs
  rule {
    api_groups = [""]
    resources  = ["pods/log"]
    verbs      = ["get"]
  }
}

# RoleBinding (binds Role to ServiceAccount)
resource "kubernetes_role_binding" "app_role_binding" {
  metadata {
    name      = "${var.app_name}-role-binding"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role.app_role.metadata[0].name
  }

  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.app_sa.metadata[0].name
    namespace = kubernetes_namespace.sample_app.metadata[0].name
  }
}

# ClusterRole example (cluster-scoped permissions)
# Uncomment if you need cluster-wide permissions
# resource "kubernetes_cluster_role" "app_cluster_role" {
#   metadata {
#     name = "${var.app_name}-cluster-role"
#     labels = {
#       app = var.app_name
#     }
#   }
#
#   rule {
#     api_groups = [""]
#     resources  = ["nodes"]
#     verbs      = ["get", "list"]
#   }
# }

# ClusterRoleBinding example
# resource "kubernetes_cluster_role_binding" "app_cluster_role_binding" {
#   metadata {
#     name = "${var.app_name}-cluster-role-binding"
#   }
#
#   role_ref {
#     api_group = "rbac.authorization.k8s.io"
#     kind      = "ClusterRole"
#     name      = kubernetes_cluster_role.app_cluster_role.metadata[0].name
#   }
#
#   subject {
#     kind      = "ServiceAccount"
#     name      = kubernetes_service_account.app_sa.metadata[0].name
#     namespace = kubernetes_namespace.sample_app.metadata[0].name
#   }
# }
