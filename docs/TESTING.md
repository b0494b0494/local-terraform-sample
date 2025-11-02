# Testing Guide

This guide explains how to test the various features implemented in this project.

## Quick Start

```bash
# Test basic app functionality
make test

# Test Redis cache (requires docker-compose)
make test-redis

# Test Kubernetes features (requires terraform apply)
make test-k8s

# Run all tests
make test-all
```

## Local Testing (Docker Compose)

### 1. Start Services

```bash
docker-compose up -d
```

### 2. Test Basic Endpoints

```bash
make test
# or
python test_app.py
```

**Tests**:
- `/health` endpoint
- `/ready` endpoint
- `/` endpoint
- `/info` endpoint

### 3. Test Redis Cache

```bash
make test-redis
# or
python test_redis_cache.py
```

**Tests**:
- Cache hit/miss behavior
- Cache statistics (`/cache/stats`)
- Cache clear (`/cache/clear`)
- Info endpoint caching

**Expected Output**:
```
Testing Redis Cache Hit/Miss
1. First request (should be MISS): ?
2. Second request (should be HIT): ?
   ? Cache HIT confirmed (same timestamp)
```

### 4. Manual Testing

**Test cache manually**:
```bash
# First request (cache MISS)
curl http://localhost:8080/

# Second request (cache HIT - same response)
curl http://localhost:8080/

# Check cache stats
curl http://localhost:8080/cache/stats

# Clear cache
curl -X POST http://localhost:8080/cache/clear
```

**Test Redis connection**:
```bash
# Check Redis is running
docker-compose ps redis

# Connect to Redis CLI
docker-compose exec redis redis-cli

# Check keys
docker-compose exec redis redis-cli KEYS "*"
```

## Kubernetes Testing

### Prerequisites

1. Kubernetes cluster running (Minikube/kind/k3d)
2. Terraform applied: `terraform apply`

### 1. Test Init Containers

```bash
# Get pod name
POD=$(kubectl get pods -n sample-app -l app=sample-app -o jsonpath='{.items[0].metadata.name}')

# Check init container status
kubectl describe pod $POD -n sample-app | grep -A 10 "Init Containers"

# View init container logs
kubectl logs $POD -n sample-app -c wait-for-redis
kubectl logs $POD -n sample-app -c validate-config
```

**Expected**: Both init containers should show "Completed" status.

### 2. Test Jobs

```bash
# List jobs
kubectl get jobs -n sample-app

# View job status
kubectl describe job sample-app-cleanup-logs -n sample-app

# View job logs
kubectl logs job/sample-app-cleanup-logs -n sample-app

# Manually trigger a job (if cleanup-logs job exists)
kubectl create job --from=cronjob/sample-app-daily-log-rotation \
  manual-cleanup-$(date +%s) -n sample-app
```

**Enable Jobs**:
```bash
terraform apply -var="enable_jobs=true"
```

### 3. Test CronJobs

```bash
# List cronjobs
kubectl get cronjobs -n sample-app

# View cronjob schedule
kubectl get cronjob sample-app-daily-log-rotation -n sample-app -o yaml

# View cronjob status
kubectl describe cronjob sample-app-daily-log-rotation -n sample-app

# List jobs created by cronjob
kubectl get jobs -n sample-app -l job-type=maintenance

# Manually trigger cronjob
kubectl create job --from=cronjob/sample-app-daily-log-rotation \
  manual-rotation-$(date +%s) -n sample-app
```

**Enable CronJobs**:
```bash
terraform apply -var="enable_cronjobs=true" -var="cronjob_schedule=0 2 * * *"
```

### 4. Test Redis in Kubernetes

```bash
# Check Redis pod
kubectl get pods -n sample-app -l app=sample-app-redis

# Connect to Redis
REDIS_POD=$(kubectl get pods -n sample-app -l app=sample-app-redis -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $REDIS_POD -n sample-app -- redis-cli

# Inside Redis CLI:
#   ping          # Should return PONG
#   keys *        # List all keys
#   get cache:*   # Get cache keys
```

### 5. Test Network Policies

**Note**: Requires CNI plugin that supports Network Policies (Calico, Cilium).

```bash
# Enable network policies
terraform apply -var="enable_network_policies=true"

# List network policies
kubectl get networkpolicies -n sample-app

# Describe a policy
kubectl describe networkpolicy sample-app-default-deny -n sample-app

# Test connectivity from pod
APP_POD=$(kubectl get pods -n sample-app -l app=sample-app -o jsonpath='{.items[0].metadata.name}')

# Should work (allowed)
kubectl exec $APP_POD -n sample-app -- nc -zv sample-app-redis 6379

# Should fail (blocked)
kubectl exec $APP_POD -n sample-app -- nc -zv google.com 80
```

### 6. Comprehensive Kubernetes Test

```bash
# Run automated tests
make test-k8s
# or
./test_k8s_features.sh
```

**Tests**:
- Namespace existence
- Init Containers status
- Jobs status
- CronJobs schedule and status
- Redis pod status

## Test Scenarios

### Scenario 1: Cache Performance Test

```bash
# Start services
docker-compose up -d

# First request (no cache)
time curl -s http://localhost:8080/ > /dev/null

# Second request (cached)
time curl -s http://localhost:8080/ > /dev/null

# Check stats
curl http://localhost:8080/cache/stats | jq '.hit_rate'
```

### Scenario 2: Init Container Dependency Test

```bash
# Deploy without Redis
terraform apply -var="enable_redis=false"

# Check init container (should not run)
kubectl describe pod <pod-name> -n sample-app | grep wait-for-redis

# Deploy with Redis
terraform apply -var="enable_redis=true"

# Check init container logs (should show Redis ready)
kubectl logs <pod-name> -n sample-app -c wait-for-redis
```

### Scenario 3: CronJob Schedule Test

```bash
# Create a test cronjob that runs every minute
terraform apply \
  -var="enable_cronjobs=true" \
  -var="cronjob_schedule=\"*/1 * * * *\""

# Wait 2 minutes
sleep 120

# Check jobs created
kubectl get jobs -n sample-app -l job-type=maintenance

# Should see multiple jobs created
```

### Scenario 4: Job Failure Handling

```bash
# Create a job that will fail
kubectl run test-job --image=busybox:1.36 --restart=OnFailure --rm -it -- false

# Check job status
kubectl get job test-job

# Should show retries
```

## Troubleshooting Tests

### Redis Tests Failing

**Problem**: `test_redis_cache.py` shows cache not working

**Solutions**:
1. Check Redis is running: `docker-compose ps redis`
2. Check app logs: `docker-compose logs sample-app`
3. Verify Redis connection in app logs: Look for "Redis connected"
4. Test Redis directly: `docker-compose exec redis redis-cli ping`

### Init Container Tests Failing

**Problem**: Init containers not running or failing

**Solutions**:
1. Check pod events: `kubectl describe pod <pod-name> -n sample-app`
2. Check init container logs: `kubectl logs <pod-name> -n sample-app -c <init-name>`
3. Verify ConfigMap exists: `kubectl get configmap -n sample-app`
4. Check if Redis is ready (for wait-for-redis): `kubectl get svc -n sample-app`

### Job Tests Failing

**Problem**: Jobs not running or stuck

**Solutions**:
1. Check job status: `kubectl describe job <job-name> -n sample-app`
2. Check pod events: `kubectl get events -n sample-app`
3. Verify resources: `kubectl describe pod <pod-name> -n sample-app`
4. Check image exists: Ensure busybox image is available

### CronJob Tests Failing

**Problem**: CronJobs not creating jobs

**Solutions**:
1. Check cronjob status: `kubectl describe cronjob <name> -n sample-app`
2. Verify schedule format: `kubectl get cronjob <name> -n sample-app -o yaml`
3. Check if suspended: `kubectl get cronjob <name> -n sample-app -o jsonpath='{.spec.suspend}'`
4. Check controller logs: `kubectl logs -n kube-system -l component=kube-controller-manager`

## Continuous Testing

### Add to CI/CD

Example GitHub Actions step:

```yaml
- name: Test Redis Cache
  run: |
    docker-compose up -d
    sleep 10
    make test-redis
```

### Pre-commit Testing

```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
make test
```

## Test Coverage

- ? Basic endpoints (health, ready, info)
- ? Redis cache (hit/miss, stats, clear)
- ? Init Containers (status, logs)
- ? Jobs (creation, status, logs)
- ? CronJobs (schedule, execution)
- ? Network Policies (connectivity)
- ??  Advanced features (requires manual testing)

## Next Steps

- Add integration tests
- Add performance benchmarks
- Add chaos engineering tests
- Add E2E tests with real workloads
