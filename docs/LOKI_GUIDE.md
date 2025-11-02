# Loki Log Aggregation Guide

This guide explains how to use Loki for centralized log aggregation.

## What is Loki?

Loki is a horizontally-scalable, highly-available log aggregation system inspired by Prometheus. It:
- Collects logs from all pods
- Indexes logs by labels (not content)
- Integrates with Grafana
- Efficient storage and querying

## Components

1. **Loki**: Log aggregation server
2. **Promtail**: Log collection agent (DaemonSet)
3. **Grafana Integration**: Query logs in Grafana

## Enabling Loki

```bash
# Enable Loki and Promtail
terraform apply -var="enable_loki=true"

# With Grafana (recommended)
terraform apply \
  -var="enable_prometheus=true" \
  -var="enable_grafana=true" \
  -var="enable_loki=true"
```

## How It Works

1. **Promtail** (DaemonSet) runs on each node
2. Collects logs from `/var/log/pods` (Kubernetes pod logs)
3. Sends logs to **Loki** via HTTP
4. **Loki** stores and indexes logs
5. **Grafana** queries logs from Loki

## Accessing Logs in Grafana

### 1. Open Grafana

```bash
kubectl port-forward -n monitoring svc/grafana 3000:3000
open http://localhost:3000
```

### 2. Explore Logs

1. Click **Explore** (compass icon)
2. Select **Loki** data source
3. Enter LogQL query (see below)
4. View logs

### 3. Create Log Dashboard

1. Create new dashboard
2. Add visualization panel
3. Select **Loki** data source
4. Use LogQL queries

## LogQL (Log Query Language)

### Basic Queries

```logql
# All logs from app namespace
{namespace="sample-app"}

# Logs from specific pod
{namespace="sample-app", pod="sample-app-xxx"}

# Logs with error
{namespace="sample-app"} |= "error"

# Logs with specific level
{namespace="sample-app"} | json | level="ERROR"

# Recent logs (last 5 minutes)
{namespace="sample-app"} [5m]
```

### Advanced Queries

```logql
# Count logs by level
sum by (level) (count_over_time({namespace="sample-app"} | json [5m]))

# Logs per second
rate({namespace="sample-app"}[1m])

# Error rate
sum(rate({namespace="sample-app"} | json | level="ERROR" [5m]))
```

## Viewing Logs

### Via Grafana

1. Go to **Explore**
2. Select **Loki** data source
3. Query: `{namespace="sample-app"}`
4. Click **Run query**
5. View logs in table or graph

### Via kubectl (Direct)

```bash
# Traditional way (still works)
kubectl logs -n sample-app <pod-name>

# Follow logs
kubectl logs -f -n sample-app <pod-name>

# All pods
kubectl logs -l app=sample-app -n sample-app
```

## Testing Log Collection

### Generate Logs

```bash
# Make some requests to generate logs
for i in {1..10}; do
  curl http://localhost:8080/
  curl -X POST http://localhost:8081/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "test log '$(date)'"}'
done
```

### Verify in Grafana

1. Open Grafana Explore
2. Query: `{namespace="sample-app"}`
3. Should see recent log entries

## Structured Logs

Your app already outputs JSON structured logs. Loki can parse them:

```logql
# Parse JSON and filter by level
{namespace="sample-app"} | json | level="INFO"

# Filter by service
{namespace="sample-app"} | json | service="llm-app"

# Extract specific fields
{namespace="sample-app"} | json | trace_id="xxx"
```

## Common Use Cases

### 1. Error Tracking

```logql
{namespace="sample-app"} | json | level="ERROR"
```

### 2. Trace Logs

```logql
{namespace="sample-app"} | json | trace_id="abc123"
```

### 3. Performance Monitoring

```logql
# Slow requests
{namespace="sample-app"} | json | duration_ms > 1000
```

### 4. Debugging Issues

```logql
# All logs from specific time
{namespace="sample-app"} [15m] | json | operation="chat_completion"
```

## Troubleshooting

### Promtail Not Collecting Logs

```bash
# Check Promtail DaemonSet
kubectl get daemonset -n monitoring promtail

# Check Promtail pods
kubectl get pods -n monitoring -l app=promtail

# View Promtail logs
kubectl logs -n monitoring -l app=promtail

# Check permissions
kubectl describe clusterrolebinding promtail
```

### Loki Not Receiving Logs

```bash
# Check Loki deployment
kubectl get deployment -n monitoring loki

# Check Loki logs
kubectl logs -n monitoring deployment/loki

# Verify service
kubectl get svc -n monitoring loki

# Test connection from Promtail
kubectl exec -n monitoring deployment/promtail -- \
  wget -q -O- http://loki:3100/ready
```

### No Logs in Grafana

1. Verify Loki data source is configured
2. Check query syntax (LogQL)
3. Verify time range
4. Check if logs exist in namespace
5. Verify Promtail is running

## Production Considerations

For production:

1. **Persistent Storage**: Use PVC for Loki data
2. **High Availability**: Run multiple Loki instances
3. **Retention Policy**: Configure log retention
4. **Compression**: Enable log compression
5. **Backup**: Regular backups of log data
6. **Indexing**: Configure appropriate indexing strategy

## Performance Tips

1. **Label Cardinality**: Keep labels low (don't use high-cardinality fields)
2. **Log Volume**: Monitor log volume and retention
3. **Query Optimization**: Use label selectors efficiently
4. **Storage**: Plan storage size based on log volume

## Next Steps

- Add Alertmanager for log-based alerts
- Create log-based dashboards
- Set up log retention policies
- Configure log parsing rules
