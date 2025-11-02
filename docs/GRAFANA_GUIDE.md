# Grafana Guide

This guide explains how to use Grafana for visualizing Prometheus metrics.

## What is Grafana?

Grafana is an open-source analytics and visualization platform. It:
- Connects to Prometheus (and other data sources)
- Creates beautiful dashboards
- Provides alerting capabilities
- Supports multiple data sources

## Enabling Grafana

```bash
# Enable both Prometheus and Grafana
terraform apply \
  -var="enable_prometheus=true" \
  -var="enable_grafana=true"

# Or set in terraform.tfvars
cat >> terraform.tfvars <<EOF
enable_prometheus = true
enable_grafana     = true
EOF
terraform apply
```

## Accessing Grafana UI

```bash
# Port forward to access Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Open in browser
open http://localhost:3000
```

## Default Credentials

?? **Change these in production!**

- **Username**: `admin`
- **Password**: `admin`

On first login, Grafana will prompt you to change the password.

## How It Works

1. **Grafana** connects to **Prometheus** as data source
2. **Prometheus** collects metrics from your apps
3. **Grafana** visualizes metrics in dashboards
4. **Dashboards** can be shared and exported

## Data Source Configuration

Prometheus data source is automatically configured:

- **Name**: Prometheus
- **Type**: Prometheus
- **URL**: http://prometheus:9090
- **Access**: Proxy

To verify:
1. Login to Grafana
2. Go to **Configuration** ? **Data Sources**
3. Verify **Prometheus** is listed and **tested**

## Creating Your First Dashboard

### Step 1: Create Dashboard

1. Click **+** ? **Create Dashboard**
2. Click **Add visualization**
3. Select **Prometheus** data source

### Step 2: Add Panel

**Query Example**:
```promql
rate(llm_requests_total[5m])
```

**Panel Settings**:
- **Title**: Request Rate
- **Unit**: requests/sec
- **Graph Type**: Time series

### Step 3: Save Dashboard

1. Click **Apply**
2. Click **Save dashboard** (top right)
3. Enter dashboard name
4. Click **Save**

## Sample Queries for Dashboards

### Request Rate
```promql
sum(rate(llm_requests_total[5m])) by (path)
```

### Response Time (p95)
```promql
histogram_quantile(0.95, 
  sum(rate(llm_request_duration_seconds_bucket[5m])) by (le)
)
```

### Error Rate
```promql
sum(rate(llm_errors_total[5m]))
```

### Tokens Generated
```promql
llm_tokens_generated_total
```

### Pod CPU Usage
```promql
sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)
```

### Pod Memory Usage
```promql
sum(container_memory_usage_bytes) by (pod)
```

## Pre-built Dashboards

### Import Kubernetes Dashboard

1. Click **+** ? **Import**
2. Enter dashboard ID: `315` (Kubernetes Cluster Monitoring)
3. Click **Load**
4. Select **Prometheus** data source
5. Click **Import**

### Import Node Exporter Dashboard

1. Import dashboard ID: `1860` (Node Exporter Full)
2. Useful for node-level metrics

### Create Custom App Dashboard

Create panels for:
- Request rate
- Error rate
- Response time
- Token generation
- Pod health

## Dashboard Best Practices

1. **Organize Panels**: Group related metrics
2. **Use Variables**: Make dashboards reusable
3. **Set Refresh Interval**: Auto-refresh (e.g., 30s)
4. **Add Alerts**: Visual thresholds
5. **Export/Share**: Save as JSON for version control

## Variables in Dashboards

Make dashboards dynamic with variables:

1. **Dashboard Settings** ? **Variables** ? **Add variable**
2. **Name**: `namespace`
3. **Type**: Query
4. **Query**: `label_values(kubernetes_namespace_name)`
5. Use in queries: `{namespace="$namespace"}`

## Alerting (Advanced)

Grafana can send alerts:

1. Create **Alert Rule** in panel
2. Set **Conditions** (thresholds)
3. Configure **Notification Channels**
4. Test alerts

## Troubleshooting

### Grafana Not Starting

```bash
# Check pod status
kubectl get pods -n monitoring -l app=grafana

# View logs
kubectl logs -n monitoring deployment/grafana

# Check resources
kubectl describe pod -n monitoring -l app=grafana
```

### Cannot Connect to Prometheus

```bash
# Verify Prometheus service
kubectl get svc -n monitoring prometheus

# Test connection from Grafana pod
kubectl exec -it -n monitoring deployment/grafana -- \
  wget -q -O- http://prometheus:9090/api/v1/targets
```

### No Data in Dashboards

1. Verify Prometheus is collecting metrics
2. Check data source connection
3. Verify query syntax
4. Check time range settings
5. Ensure metrics exist in Prometheus

## Production Considerations

For production:

1. **Persistent Storage**: Use PVC for Grafana data
2. **Authentication**: Integrate with LDAP/OAuth
3. **RBAC**: Configure user permissions
4. **Backup**: Export dashboards regularly
5. **High Availability**: Run multiple Grafana instances
6. **Security**: Change default password, use HTTPS

## Next Steps

- Add Alertmanager for alerting
- Create custom dashboards
- Set up dashboard provisioning
- Add more data sources (Loki for logs)
