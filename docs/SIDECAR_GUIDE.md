# Sidecar Pattern Guide

This guide explains the Sidecar pattern and how it's implemented in this project.

## What is the Sidecar Pattern?

The Sidecar pattern uses **multiple containers in a single pod** that share resources and work together. The main container handles the application logic, while sidecar containers provide supporting functionality.

## Architecture

```
Pod
??? Main Container (sample-app)
?   ??? Application logic
?   ??? Writes logs to /app/logs
?
??? Sidecar: Log Shipper
?   ??? Reads logs from /shared/logs
?   ??? Ships to external system (Loki, ELK, etc.)
?
??? Sidecar: Metrics Exporter
    ??? Collects metrics from shared volume
    ??? Exports to Prometheus, etc.
    
Shared Volume (emptyDir)
??? /shared/logs (accessible by all containers)
```

## Sidecars in This Project

### 1. Log Shipper Sidecar

**Purpose**: Collects and ships application logs to external systems.

**Features**:
- Monitors log files in `/shared/logs`
- Continuously processes logs
- Can ship to Loki, ELK stack, CloudWatch, etc.

**Resource Usage**:
- CPU: 50m request, 200m limit
- Memory: 64Mi request, 128Mi limit

**Enable**:
```bash
terraform apply -var="enable_sidecar_log_shipper=true"
```

### 2. Metrics Exporter Sidecar

**Purpose**: Collects and exports metrics to monitoring systems.

**Features**:
- Collects metrics from shared volume
- Exports to Prometheus, StatsD, etc.
- Runs on configurable schedule

**Resource Usage**:
- CPU: 50m request, 200m limit
- Memory: 64Mi request, 128Mi limit

**Enable**:
```bash
terraform apply -var="enable_sidecar_metrics=true"
```

## Shared Storage

### emptyDir Volume

Both sidecars and the main container share an `emptyDir` volume:

```hcl
volume {
  name = "shared-logs"
  empty_dir {
    medium     = "Memory"
    size_limit = "100Mi"
  }
}
```

**Characteristics**:
- **Memory-backed**: Fast, ephemeral storage
- **Pod-scoped**: Exists only for the pod's lifetime
- **Shared**: All containers in pod can access it
- **Size limit**: 100Mi to prevent memory exhaustion

**Mount Points**:
- Main container: `/app/logs` (writes logs)
- Log shipper: `/shared/logs` (reads logs)
- Metrics exporter: `/shared/metrics` (reads metrics)

## Benefits of Sidecar Pattern

### 1. Separation of Concerns
- Main container: Application logic only
- Sidecars: Cross-cutting concerns (logging, metrics)

### 2. Reusability
- Same sidecar image across multiple applications
- Standardized log shipping/metrics collection

### 3. Independence
- Sidecars can fail without affecting main app
- Can update sidecars independently

### 4. Resource Sharing
- Shared volumes for data exchange
- Same network namespace
- Shared lifecycle (start/stop together)

## Usage

### Enable Sidecars

```bash
# Enable log shipper only
terraform apply \
  -var="enable_sidecar_log_shipper=true"

# Enable both sidecars
terraform apply \
  -var="enable_sidecar_log_shipper=true" \
  -var="enable_sidecar_metrics=true"
```

### View Sidecar Logs

```bash
# Get pod name
POD=$(kubectl get pods -n sample-app -l app=sample-app -o jsonpath='{.items[0].metadata.name}')

# View log shipper logs
kubectl logs $POD -n sample-app -c log-shipper

# View metrics exporter logs
kubectl logs $POD -n sample-app -c metrics-exporter
```

### Check Container Status

```bash
# Describe pod to see all containers
kubectl describe pod $POD -n sample-app | grep -A 5 "Containers:"

# Should show:
# - sample-app (main)
# - log-shipper (sidecar)
# - metrics-exporter (sidecar)
```

## Real-World Examples

### Log Shipping to Loki

In production, the log shipper would:

```bash
# Install promtail or similar
# Configure to read from /shared/logs
# Ship to Loki endpoint
```

### Metrics to Prometheus

The metrics exporter would:

```bash
# Collect metrics from /shared/metrics
# Format as Prometheus metrics
# Push to Prometheus gateway or expose /metrics endpoint
```

## Advanced Patterns

### 1. Multiple Log Shippers

Ship to multiple destinations:

```hcl
sidecar "log-shipper-loki" { ... }
sidecar "log-shipper-cloudwatch" { ... }
```

### 2. Configurable Sidecars

Pass configuration via ConfigMap:

```hcl
env {
  name = "LOKI_ENDPOINT"
  value_from {
    config_map_key_ref { ... }
  }
}
```

### 3. Sidecar for Service Mesh

Service mesh proxies (Istio, Linkerd) use sidecars:

```
Pod
??? App Container
??? Service Mesh Proxy (sidecar)
    ??? Handles traffic routing, mTLS, etc.
```

## Troubleshooting

### Sidecar Not Starting

**Check**:
```bash
kubectl describe pod $POD -n sample-app
kubectl logs $POD -n sample-app -c log-shipper
```

**Common issues**:
- Resource limits too low
- Image pull errors
- Volume mount issues

### Sidecar Using Too Much Memory

**Symptoms**: Pod OOMKilled

**Solutions**:
- Increase memory limits
- Reduce log buffer size
- Use smaller sidecar images

### Logs Not Appearing

**Check**:
```bash
# Verify main container writes logs
kubectl exec $POD -n sample-app -c sample-app -- ls -la /app/logs

# Check sidecar can read
kubectl exec $POD -n sample-app -c log-shipper -- ls -la /shared/logs
```

## Best Practices

### 1. Resource Limits

Always set limits for sidecars:
```hcl
resources {
  limits = {
    cpu    = "200m"
    memory = "128Mi"
  }
}
```

### 2. Health Checks

Add health checks to sidecars:
```hcl
liveness_probe {
  exec {
    command = ["check-sidecar-health.sh"]
  }
}
```

### 3. Graceful Shutdown

Ensure sidecars handle termination signals:
```bash
trap 'cleanup; exit 0' SIGTERM
```

### 4. Log Rotation

Rotate logs to prevent disk full:
```bash
# Use logrotate or similar
# Limit log file sizes
```

## Comparison with Alternatives

| Pattern | Use Case | Complexity |
|---------|----------|------------|
| **Sidecar** | Log shipping, metrics | Medium |
| **DaemonSet** | Node-level logging | Low |
| **Service Mesh** | Traffic management | High |
| **Separate Pods** | Independent scaling | Low |

## Next Steps

- Integrate with real log aggregation (Loki)
- Add Prometheus metrics export
- Implement health checks for sidecars
- Add configuration via ConfigMap
