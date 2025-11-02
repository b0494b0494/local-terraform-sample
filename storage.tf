# Persistent Volume and Persistent Volume Claim
# Provides persistent storage for stateful applications

# StorageClass (for dynamic provisioning)
resource "kubernetes_storage_class" "local_storage" {
  metadata {
    name = "local-storage"
  }

  storage_provisioner = "kubernetes.io/no-provisioner"
  volume_binding_mode = "WaitForFirstConsumer"
}

# PersistentVolume (local storage example)
# Note: For local emulators, this uses hostPath
# In production, use cloud storage (EBS, Azure Disk, etc.)
resource "kubernetes_persistent_volume" "app_storage" {
  count = var.enable_persistent_storage ? 1 : 0

  metadata {
    name = "${var.app_name}-pv"
    labels = {
      app = var.app_name
      env = var.environment
    }
  }

  spec {
    capacity = {
      storage = var.storage_size
    }

    access_modes = ["ReadWriteOnce"]
    persistent_volume_reclaim_policy = "Retain"

    # For local environments (Minikube/kind)
    # In production, use CSI driver for cloud storage
    host_path {
      path = var.storage_host_path
      type = "DirectoryOrCreate"
    }

    # Uncomment for production with cloud storage:
    # csi {
    #   driver       = "ebs.csi.aws.com"  # AWS example
    #   volume_handle = "..."
    # }

    storage_class_name = kubernetes_storage_class.local_storage.metadata[0].name
  }
}

# PersistentVolumeClaim (what the app uses)
resource "kubernetes_persistent_volume_claim" "app_storage" {
  count = var.enable_persistent_storage ? 1 : 0

  metadata {
    name      = "${var.app_name}-pvc"
    namespace = kubernetes_namespace.sample_app.metadata[0].name
    labels = {
      app = var.app_name
      env = var.environment
    }
  }

  spec {
    access_modes       = ["ReadWriteOnce"]
    storage_class_name = kubernetes_storage_class.local_storage.metadata[0].name

    resources {
      requests = {
        storage = var.storage_size
      }
    }

    # Bind to specific PV (optional - remove for dynamic provisioning)
    # volume_name = kubernetes_persistent_volume.app_storage[0].metadata[0].name
  }
}
