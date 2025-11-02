# Blue-Green Deployment Guide

This guide explains how to use the blue-green deployment strategy for zero-downtime deployments.

## What is Blue-Green Deployment?

Blue-Green deployment is a strategy that:
- Maintains two identical production environments (blue and green)
- Routes traffic to one environment (active)
- Allows you to deploy new version to inactive environment
- Switch traffic instantly with zero downtime
- Rollback quickly by switching back

## Enabling Blue-Green Deployment

```bash
# Set in terraform.tfvars
enable_blue_green = true
active_environment = "blue"  # or "green"
```

```bash
# Apply configuration
terraform apply
```

## How It Works

1. **Two Environments**: Blue and green deployments run simultaneously
2. **Traffic Routing**: Main service (`sample-app-main`) routes to active environment
3. **Testing**: You can test inactive environment independently
4. **Switch**: Change `active_environment` to switch traffic
5. **Rollback**: Switch back to previous environment if issues occur

## Deployment Workflow

### 1. Initial Setup (Blue Active)

```bash
# Deploy with blue as active
terraform apply -var="enable_blue_green=true" -var="active_environment=blue"
```

### 2. Deploy New Version to Green

```bash
# Update image tag
terraform apply \
  -var="enable_blue_green=true" \
  -var="active_environment=blue" \
  -var="app_image_tag=v2.0.0"
```

Green environment will be updated with new version while blue remains active.

### 3. Test Green Environment

```bash
# Port forward to green service for testing
kubectl port-forward -n sample-app svc/sample-app-green 8080:8080

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/info
```

### 4. Switch Traffic to Green

```bash
# Use switch script
./scripts/blue-green-switch.sh

# Or manually
terraform apply -var="active_environment=green"
```

### 5. Monitor and Verify

```bash
# Check active pods
kubectl get pods -n sample-app -l environment=green

# Check service endpoints
kubectl get endpoints -n sample-app sample-app-main

# Check logs
kubectl logs -n sample-app -l environment=green --tail=50
```

### 6. Rollback if Needed

```bash
# Quick rollback script
./scripts/blue-green-rollback.sh

# Or manually switch back
terraform apply -var="active_environment=blue"
```

## Scripts

### Switch Script

```bash
./scripts/blue-green-switch.sh
```

Automatically switches between blue and green environments.

### Rollback Script

```bash
./scripts/blue-green-rollback.sh
```

Quickly rolls back to the previous environment.

## Manual Operations

### Check Current Active Environment

```bash
terraform output active_environment
```

### Switch Environment Manually

```bash
# Switch to green
terraform apply -var="active_environment=green"

# Switch to blue
terraform apply -var="active_environment=blue"
```

### Access Inactive Environment Directly

```bash
# Access green environment (even if blue is active)
kubectl port-forward -n sample-app svc/sample-app-green 8081:8080

# Access blue environment
kubectl port-forward -n sample-app svc/sample-app-blue 8082:8080
```

## Best Practices

1. **Always Test Inactive Environment**: Test new version before switching
2. **Monitor During Switch**: Watch metrics and logs after switching
3. **Keep Previous Version**: Don't delete inactive environment immediately
4. **Gradual Traffic Split**: For production, consider gradual traffic shifting (not implemented in this basic version)
5. **Health Checks**: Ensure health checks pass before switching

## Troubleshooting

### Service Not Routing Correctly

```bash
# Check service selector
kubectl describe svc -n sample-app sample-app-main

# Check deployment labels
kubectl get deployment -n sample-app -o yaml | grep -A 5 labels
```

### Pods Not Ready

```bash
# Check pod status
kubectl get pods -n sample-app -l environment=green

# Check events
kubectl describe pod -n sample-app <pod-name>

# Check logs
kubectl logs -n sample-app <pod-name>
```

### Rollback Not Working

```bash
# Verify terraform state
terraform state list | grep blue

# Force refresh
terraform refresh

# Re-apply with correct environment
terraform apply -var="active_environment=blue" -refresh=true
```

## Advanced Features (Future)

- Traffic splitting (e.g., 90% blue, 10% green)
- Automated health checks before switch
- Automatic rollback on errors
- Canary deployments
- Integration with service mesh (Istio)

## Example: Full Deployment Cycle

```bash
# 1. Current state: Blue active, v1.0.0
terraform apply -var="enable_blue_green=true" -var="active_environment=blue"

# 2. Deploy v2.0.0 to green
terraform apply \
  -var="enable_blue_green=true" \
  -var="active_environment=blue" \
  -var="app_image_tag=v2.0.0"

# 3. Test green
kubectl port-forward -n sample-app svc/sample-app-green 8080:8080
# ... test endpoints ...

# 4. Switch to green
./scripts/blue-green-switch.sh

# 5. Monitor (wait 5 minutes)
kubectl get pods -n sample-app -w

# 6. If issues, rollback
./scripts/blue-green-rollback.sh
```

---

**Note**: This is a simplified implementation for learning. Production blue-green deployments may include additional features like automated testing, gradual traffic shifting, and integration with CI/CD pipelines.
