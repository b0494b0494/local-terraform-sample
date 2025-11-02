# Persistent Storage Guide

This guide explains how to use Persistent Volumes (PV) and Persistent Volume Claims (PVC) for data persistence.

## What is Persistent Storage?

In Kubernetes, pods are ephemeral - when they restart or are deleted, any data stored in the container filesystem is lost. Persistent Volumes allow data to survive pod restarts and deletions.

## Components

1. **StorageClass**: Defines storage provisioning behavior
2. **PersistentVolume (PV)**: Cluster-level storage resource
3. **PersistentVolumeClaim (PVC)**: Pod-level request for storage

## Configuration

### Enable Persistent Storage

```bash
# Enable storage
terraform apply -var="enable_persistent_storage=true"

# With custom size
terraform apply \
  -var="enable_persistent_storage=true" \
  -var="storage_size=5Gi" \
  -var="storage_host_path=/data/k8s-storage"
```

### Variables

- `enable_persistent_storage`: Enable/disable storage (default: false)
- `storage_size`: Storage size (e.g., "1Gi", "10Gi", "100Gi")
- `storage_host_path`: Local path for storage (Minikube/kind)

## How It Works

1. **StorageClass** is created to define provisioning behavior
2. **PersistentVolume** provides cluster storage (local hostPath for emulators)
3. **PersistentVolumeClaim** requests storage from PV
4. **Pod** mounts PVC as a volume at `/app/data`

## Viewing Storage Resources

```bash
# List StorageClasses
kubectl get storageclass

# List PersistentVolumes
kubectl get pv

# List PersistentVolumeClaims
kubectl get pvc -n <app-name>

# Detailed view
kubectl describe pv <pv-name>
kubectl describe pvc <pvc-name> -n <app-name>
```

## Using Storage in Your App

Once enabled, data stored at `/app/data` in the container will persist:

```python
# Example: app.py
import os

DATA_DIR = os.getenv('DATA_DIR', '/app/data')

def save_data(filename, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w') as f:
        f.write(data)

def load_data(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read()
    return None
```

## Testing Persistence

### 1. Write Data to Volume

```bash
# Exec into pod
kubectl exec -it -n <app-name> <pod-name> -- sh

# Create test file
echo "test data" > /app/data/test.txt
cat /app/data/test.txt

# Exit pod
exit
```

### 2. Delete Pod

```bash
# Delete pod (HPA will recreate it)
kubectl delete pod <pod-name> -n <app-name>

# Wait for new pod
kubectl get pods -n <app-name> -w
```

### 3. Verify Data Persists

```bash
# Check data in new pod
kubectl exec -it -n <app-name> <new-pod-name> -- cat /app/data/test.txt
# Should still show: test data
```

## Storage Access Modes

- **ReadWriteOnce (RWO)**: Single node read/write
- **ReadOnlyMany (ROX)**: Multiple nodes read-only
- **ReadWriteMany (RWX)**: Multiple nodes read/write

Current configuration uses **ReadWriteOnce** (RWO).

## For Production

?? **Local hostPath is for development only!** For production:

### AWS EKS
```hcl
storage_class {
  provisioner = "ebs.csi.aws.com"
  parameters = {
    type = "gp3"
    fsType = "ext4"
  }
}
```

### Google GKE
```hcl
storage_class {
  provisioner = "pd.csi.storage.gke.io"
  parameters = {
    type = "pd-standard"
  }
}
```

### Azure AKS
```hcl
storage_class {
  provisioner = "disk.csi.azure.com"
  parameters = {
    skuName = "Standard_LRS"
  }
}
```

## Common Issues

### PVC Pending

**Cause**: No available PV or StorageClass mismatch

**Solution**:
```bash
# Check PVC status
kubectl describe pvc <pvc-name> -n <app-name>

# Check if PV exists
kubectl get pv

# For local storage, ensure host path exists
mkdir -p /tmp/k8s-storage
```

### Volume Not Mounting

**Cause**: Pod spec missing volume mount

**Solution**: Verify volume mount in deployment:
```bash
kubectl describe pod <pod-name> -n <app-name> | grep -A 10 "Mounts"
```

### Permission Denied

**Cause**: File permissions on host path

**Solution**:
```bash
# Set permissions on host path
sudo chmod 777 /tmp/k8s-storage

# Or run container as specific user
security_context {
  run_as_user = 1000
  fs_group    = 1000
}
```

## Best Practices

1. **Use StorageClass**: Let Kubernetes handle provisioning dynamically
2. **Set Appropriate Size**: Don't request more than needed
3. **Backup Strategy**: Regular backups of persistent data
4. **Monitor Usage**: Watch storage usage and growth
5. **Clean Up**: Delete PVCs when no longer needed (data may persist)

## Stateful Applications

For stateful applications (databases, etc.), consider:

- **StatefulSets**: Better for stateful apps with stable network identity
- **Replication**: Multiple replicas with shared or replicated storage
- **Backup/Restore**: Regular backup strategies

## Next Steps

- StatefulSet for databases
- Volume snapshots for backup
- Storage quotas and limits
- Dynamic provisioning examples
