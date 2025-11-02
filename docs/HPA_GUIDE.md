# Horizontal Pod Autoscaler (HPA) Guide

This guide explains how to use the Horizontal Pod Autoscaler feature.

## What is HPA?

Horizontal Pod Autoscaler automatically adjusts the number of pod replicas based on CPU and memory usage. This ensures your application scales up during high load and scales down during low load, optimizing resource usage.

## How It Works

1. **Metrics Collection**: HPA monitors CPU/memory usage of pods
2. **Decision Making**: Compares current usage with target threshold
3. **Scaling**: Adds or removes pods to maintain target utilization
4. **Behavior Control**: Configures how fast/slow scaling happens

## Configuration

### Basic Settings

```hcl
# In terraform.tfvars or variables
enable_hpa       = true      # Enable/disable HPA
hpa_min_replicas = 2         # Minimum pods (even at low load)
hpa_max_replicas = 10        # Maximum pods (prevents runaway scaling)
hpa_target_cpu   = 70        # Target CPU utilization %
```

### Apply HPA

```bash
# With defaults (HPA enabled)
terraform apply

# Disable HPA
terraform apply -var="enable_hpa=false"

# Custom configuration
terraform apply \
  -var="hpa_min_replicas=3" \
  -var="hpa_max_replicas=20" \
  -var="hpa_target_cpu=80"
```

## Behavior Explained

### Scale Down
- **Stabilization Window**: 300 seconds (5 minutes)
- **Policy**: Reduce by 50% every 60 seconds
- **Purpose**: Prevents aggressive scale-down during temporary dips

### Scale Up
- **Stabilization Window**: 0 seconds (immediate)
- **Policies**: 
  - Scale by 100% every 15 seconds (percentage-based)
  - Add 2 pods every 60 seconds (pod-based)
- **Select Policy**: Max (uses whichever scales more)
- **Purpose**: Quick response to traffic spikes

## Monitoring HPA

### Check HPA Status

```bash
# View HPA
kubectl get hpa -n <app-name>

# Detailed view
kubectl describe hpa <app-name>-hpa -n <app-name>

# Watch HPA in real-time
watch kubectl get hpa -n <app-name>
```

### Check Current Metrics

```bash
# View current pod metrics (requires metrics-server)
kubectl top pods -n <app-name>

# View node metrics
kubectl top nodes
```

## Testing HPA

### Generate Load to Test Scaling

```bash
# Method 1: Use a load testing tool
kubectl run -i --tty load-generator --rm \
  --image=busybox --restart=Never -- \
  /bin/sh -c "while true; do wget -q -O- http://sample-app-service:80; done"

# Method 2: Multiple parallel requests
for i in {1..10}; do
  kubectl run load-test-$i --image=busybox --restart=Never \
    -- /bin/sh -c "while true; do wget -q -O- http://sample-app-service:80; sleep 0.1; done" &
done
```

### Monitor Scaling

```bash
# In one terminal, watch HPA
watch kubectl get hpa -n sample-app

# In another terminal, watch pods
watch kubectl get pods -n sample-app
```

### Clean Up Load Generators

```bash
kubectl delete pod load-generator
# or delete all load-test pods
kubectl delete pod -l run=load-test
```

## Prerequisites

HPA requires **metrics-server** to be installed:

### Minikube
```bash
# Metrics-server is usually enabled by default
minikube addons enable metrics-server
```

### kind
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Verify Metrics Server

```bash
# Check if metrics-server is running
kubectl get deployment metrics-server -n kube-system

# Test metrics
kubectl top nodes
```

## Common Issues

### HPA shows "unknown" for metrics

**Cause**: Metrics-server not installed or not working

**Solution**:
```bash
# Check metrics-server
kubectl get apiservice v1beta1.metrics.k8s.io

# View metrics-server logs
kubectl logs -n kube-system deployment/metrics-server
```

### HPA not scaling

**Causes**:
1. CPU requests not set in Deployment
2. Metrics-server not working
3. Target CPU too high/low

**Solutions**:
```bash
# Verify CPU requests are set
kubectl describe deployment <app-name> -n <app-name> | grep -A 5 "Limits\|Requests"

# Adjust target CPU
terraform apply -var="hpa_target_cpu=50"  # Lower threshold
```

### Pods scaling too aggressively

**Solution**: Adjust behavior policies in `hpa.tf`:
- Increase `stabilization_window_seconds` for scale-down
- Reduce `value` in scale-up policies

## Best Practices

1. **Set Appropriate Limits**: Always set CPU/memory requests and limits
2. **Test Scaling**: Load test to verify HPA works as expected
3. **Monitor First**: Watch HPA behavior before adjusting thresholds
4. **Conservative Scaling**: Start with conservative limits, adjust based on metrics
5. **Consider Cost**: Higher max replicas = higher costs

## Next Steps

- Add custom metrics support (metrics beyond CPU/memory)
- Add Vertical Pod Autoscaler (VPA) for resource optimization
- Combine with Cluster Autoscaler for node-level scaling
