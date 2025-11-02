# Prometheus Monitoring Guide

This guide explains how to use Prometheus for metrics collection and monitoring.

## What is Prometheus?

Prometheus is an open-source monitoring and alerting toolkit. It:
- Collects metrics from applications
- Stores metrics in a time-series database
- Provides query language (PromQL) for analysis
- Supports alerting rules

## Enabling Prometheus

```bash
# Enable Prometheus monitoring
terraform apply -var="enable_prometheus=true"

# Or set in terraform.tfvars
echo 'enable_prometheus = true' >> terraform.tfvars
terraform apply
```

## Accessing Prometheus UI

```bash
# Port forward to access Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Open in browser
open http://localhost:9090
```

## How It Works

1. **App Exposes Metrics**: Your app already has `/metrics` endpoint
2. **Prometheus Scrapes**: Prometheus discovers pods via annotations
3. **Metrics Stored**: Metrics stored in Prometheus time-series DB
4. **Query & Visualize**: Use PromQL to query metrics

## Pod Annotations

Pods are automatically annotated when Prometheus is enabled:

```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8080"
  prometheus.io/path: "/metrics"
```

Prometheus uses these annotations to discover and scrape metrics.

## Prometheus Configuration

Prometheus config is stored in a ConfigMap:

```bash
# View Prometheus config
kubectl get configmap prometheus-config -n monitoring -o yaml

# Check Prometheus logs
kubectl logs -n monitoring deployment/prometheus
```

## Using Prometheus UI

### 1. Check Targets

1. Go to Prometheus UI: http://localhost:9090
2. Click **Status** ? **Targets**
3. Verify `sample-app` target is **UP**

### 2. Query Metrics

Use PromQL (Prometheus Query Language):

```promql
# Total HTTP requests
sum(rate(llm_requests_total[5m]))

# Request duration (p95)
histogram_quantile(0.95, llm_request_duration_seconds_bucket)

# Error rate
sum(rate(llm_errors_total[5m]))

# Pod count
count(kube_pod_info{namespace="sample-app"})
```

### 3. View Metrics

Click **Graph** tab, enter query, click **Execute**:

- `llm_requests_total` - Total requests
- `llm_tokens_generated_total` - Tokens generated
- `llm_errors_total` - Error count

## Testing Metrics Collection

### Generate Load

```bash
# Generate some requests
for i in {1..100}; do
  curl http://localhost:8080/ > /dev/null 2>&1
done

# Or use the LLM app
for i in {1..50}; do
  curl -X POST http://localhost:8081/chat \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"test $i\"}" > /dev/null 2>&1
done
```

### Verify in Prometheus

1. Open Prometheus UI
2. Query: `rate(llm_requests_total[1m])`
3. Should show increasing metrics

## Common PromQL Queries

### Application Metrics

```promql
# Request rate (requests per second)
rate(llm_requests_total[5m])

# Average response time
rate(llm_request_duration_seconds_avg[5m])

# Error rate
rate(llm_errors_total[5m])

# Total tokens
llm_tokens_generated_total
```

### Kubernetes Metrics

```promql
# Pod CPU usage
rate(container_cpu_usage_seconds_total[5m])

# Pod memory usage
container_memory_usage_bytes

# Pod count by namespace
count(kube_pod_info) by (namespace)
```

## Alerts (Future)

Alerts can be configured in Prometheus:

```yaml
groups:
  - name: app_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(llm_errors_total[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate detected"
```

## Troubleshooting

### Targets Showing as DOWN

**Check**:
```bash
# Verify pod annotations
kubectl get pod -n sample-app -o yaml | grep prometheus.io

# Check metrics endpoint
kubectl exec -n sample-app <pod-name> -- curl localhost:8080/metrics

# Check Prometheus config
kubectl logs -n monitoring deployment/prometheus
```

### Metrics Not Appearing

1. Verify app exposes `/metrics` endpoint
2. Check Prometheus target status
3. Verify scrape interval (15s default)
4. Check Prometheus logs for errors

### Prometheus Not Starting

```bash
# Check Prometheus pod status
kubectl get pods -n monitoring

# View logs
kubectl logs -n monitoring deployment/prometheus

# Check resources
kubectl describe pod -n monitoring -l app=prometheus
```

## Production Considerations

For production, consider:

1. **Prometheus Operator**: Easier management
2. **High Availability**: Run multiple Prometheus instances
3. **High Availability**: Run multiple Prometheus instances
4. **Remote Storage**: Long-term retention (e.g., Thanos)
5. **Alertmanager**: Alert routing and notification
6. **Recording Rules**: Pre-computed queries for performance

## Next Steps

- Add Grafana for visualization
- Add Alertmanager for alerting
- Add ServiceMonitor (Prometheus Operator)
- Add custom metrics to applications
