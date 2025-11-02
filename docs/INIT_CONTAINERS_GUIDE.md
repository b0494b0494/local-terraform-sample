# Init Containers Guide

This guide explains how Init Containers work and how they're used in this project.

## What are Init Containers?

Init Containers are specialized containers that run **before** the main application containers start. They must complete successfully before the pod's main containers begin execution.

## Use Cases

1. **Wait for dependencies**: Ensure external services (Redis, databases) are ready
2. **Configuration validation**: Verify settings before app starts
3. **Database migrations**: Run schema updates before app connects
4. **Data preparation**: Download files, initialize directories
5. **Security setup**: Fetch secrets, configure certificates

## Init Containers in This Project

### 1. wait-for-redis

**Purpose**: Ensures Redis is ready before the application starts.

**When it runs**: Only when `enable_redis = true`

**What it does**:
- Uses `netcat` (nc) to check if Redis service is accessible
- Polls every 2 seconds until Redis responds
- Exits successfully when Redis is ready
- Fails if Redis never becomes available (prevents app from starting)

**Implementation**:
```hcl
init_container {
  name  = "wait-for-redis"
  image = "busybox:1.36"
  command = ["sh", "-c", "until nc -z sample-app-redis 6379; do sleep 2; done"]
}
```

### 2. validate-config

**Purpose**: Validates required configuration before application starts.

**When it runs**: Always (every pod startup)

**What it does**:
- Reads `APP_NAME` and `APP_VERSION` from ConfigMap
- Verifies they are not empty
- Exits with error if validation fails
- Ensures configuration integrity

**Implementation**:
```hcl
init_container {
  name  = "validate-config"
  image = "busybox:1.36"
  command = ["sh", "-c", "if [ -z \"$APP_NAME\" ]; then exit 1; fi"]
  env {
    name = "APP_NAME"
    value_from {
      config_map_key_ref { ... }
    }
  }
}
```

## How Init Containers Work

### Execution Order

1. **All init containers run sequentially** (one after another)
2. **Each must succeed** (exit code 0) before next starts
3. **Main containers start** only after all init containers complete
4. **If any init container fails**, the pod is marked as failed

### Lifecycle

```
Pod Created
    ?
Init Container 1 (wait-for-redis)
    ? (success)
Init Container 2 (validate-config)
    ? (success)
Main Container (sample-app)
    ?
Pod Running
```

## Viewing Init Container Status

### Check Init Container Logs

```bash
# View all containers in a pod
kubectl get pod <pod-name> -n sample-app -o jsonpath='{.spec.initContainers[*].name}'

# View init container logs
kubectl logs <pod-name> -n sample-app -c wait-for-redis
kubectl logs <pod-name> -n sample-app -c validate-config
```

### Check Pod Status

```bash
# See init container status
kubectl describe pod <pod-name> -n sample-app

# Output shows:
# Init Containers:
#   wait-for-redis:
#     State:          Terminated
#       Reason:       Completed
#       Exit Code:    0
```

## Common Patterns

### Pattern 1: Wait for Service

Wait for a service to be ready:

```hcl
init_container {
  name  = "wait-for-service"
  image = "busybox:1.36"
  command = [
    "sh", "-c",
    "until nc -z service-name 8080; do echo waiting...; sleep 2; done"
  ]
}
```

### Pattern 2: Validate Secrets

Ensure secrets exist:

```hcl
init_container {
  name  = "check-secrets"
  image = "busybox:1.36"
  command = [
    "sh", "-c",
    "if [ -z \"$API_KEY\" ]; then exit 1; fi"
  ]
  env {
    name = "API_KEY"
    value_from {
      secret_key_ref {
        name = "app-secret"
        key  = "api_key"
      }
    }
  }
}
```

### Pattern 3: Database Migration

Run database migrations (future task):

```hcl
init_container {
  name  = "migrate-db"
  image = "app-image:latest"
  command = ["python", "migrate.py"]
  env {
    name = "DATABASE_URL"
    value_from { ... }
  }
}
```

## Troubleshooting

### Init Container Failing

**Symptom**: Pod stuck in `Init:0/2` or `Init:Error`

**Check**:
```bash
# View init container logs
kubectl logs <pod-name> -n sample-app -c wait-for-redis

# Check pod events
kubectl describe pod <pod-name> -n sample-app
```

**Common Causes**:
- Redis not ready yet ? wait or check Redis deployment
- Configuration missing ? verify ConfigMap exists
- Network issues ? check Network Policies
- Image pull errors ? verify image exists

### Init Container Taking Too Long

**Symptom**: Pod stuck in `Init` state for a long time

**Solutions**:
- Increase timeout in wait loop
- Check if dependency service is actually running
- Verify DNS resolution works

### Debugging Tips

1. **Check init container logs first**:
   ```bash
   kubectl logs <pod> -c <init-container-name>
   ```

2. **Describe pod for detailed status**:
   ```bash
   kubectl describe pod <pod-name>
   ```

3. **Test connectivity manually**:
   ```bash
   kubectl run -it debug --image=busybox:1.36 --rm -- sh
   # Inside pod: nc -zv service-name 6379
   ```

## Best Practices

1. **Keep init containers lightweight**: Use small images (busybox, alpine)
2. **Add retries**: Don't fail immediately, retry with backoff
3. **Timeout logic**: Don't wait indefinitely
4. **Clear error messages**: Log helpful debugging info
5. **Idempotent operations**: Can be safely retried

## Advanced: Shared Volumes

Init containers can prepare data in shared volumes:

```hcl
init_container {
  name  = "prepare-data"
  image = "busybox:1.36"
  command = ["sh", "-c", "echo 'data' > /shared/data.txt"]
  
  volume_mount {
    name       = "shared-data"
    mount_path = "/shared"
  }
}

container {
  name = "app"
  # ... app config ...
  
  volume_mount {
    name       = "shared-data"
    mount_path = "/app/data"  # Can access data.txt here
  }
}
```

## Next Steps

- Implement database migration init container (Task 1.1)
- Add health check init containers
- Explore more complex dependency chains
