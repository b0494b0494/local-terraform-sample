# Prometheus Alerting Rules
# Defines alerts for application health, errors, and performance

resource "kubernetes_config_map" "prometheus_alerts" {
  count = var.enable_prometheus ? 1 : 0

  metadata {
    name      = "prometheus-alerts"
    namespace = kubernetes_namespace.monitoring.metadata[0].name
    labels = {
      app = "prometheus"
    }
  }

  data = {
    "sample-app-alerts.yml" = <<-EOF
      groups:
        - name: sample-app-health
          interval: 30s
          rules:
            # Alert: Application Down
            - alert: AppDown
              expr: up{job="sample-app"} == 0
              for: 1m
              labels:
                severity: critical
                service: sample-app
              annotations:
                summary: "Application is down"
                description: "Sample app has been down for more than 1 minute. Pod: {{ $labels.pod }}"

            # Alert: High Error Rate
            - alert: HighErrorRate
              expr: |
                sum(rate(http_requests_total{status=~"5.."}[5m])) 
                / 
                sum(rate(http_requests_total[5m])) 
                > 0.05
              for: 5m
              labels:
                severity: warning
                service: sample-app
              annotations:
                summary: "High error rate detected"
                description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

            # Alert: High Request Latency (p95)
            - alert: HighLatency
              expr: |
                histogram_quantile(0.95, 
                  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
                ) > 1.0
              for: 5m
              labels:
                severity: warning
                service: sample-app
              annotations:
                summary: "High request latency"
                description: "95th percentile latency is {{ $value }}s (threshold: 1.0s)"

            # Alert: Low Request Rate (Possible Issue)
            - alert: LowRequestRate
              expr: sum(rate(http_requests_total[5m])) < 0.1
              for: 10m
              labels:
                severity: info
                service: sample-app
              annotations:
                summary: "Low request rate"
                description: "Request rate is {{ $value }} req/s (threshold: 0.1 req/s)"

            # Alert: Pod Restarting Frequently
            - alert: PodRestarting
              expr: |
                rate(kube_pod_container_status_restarts_total{namespace="sample-app"}[15m]) > 0
              for: 5m
              labels:
                severity: warning
                service: sample-app
              annotations:
                summary: "Pod restarting frequently"
                description: "Pod {{ $labels.pod }} has restarted {{ $value }} times in the last 15 minutes"

            # Alert: High Memory Usage
            - alert: HighMemoryUsage
              expr: |
                (container_memory_working_set_bytes{namespace="sample-app"} 
                 / 
                 container_spec_memory_limit_bytes{namespace="sample-app"}) 
                > 0.9
              for: 5m
              labels:
                severity: warning
                service: sample-app
              annotations:
                summary: "High memory usage"
                description: "Pod {{ $labels.pod }} memory usage is {{ $value | humanizePercentage }}"

            # Alert: High CPU Usage
            - alert: HighCPUUsage
              expr: |
                (rate(container_cpu_usage_seconds_total{namespace="sample-app"}[5m]) 
                 / 
                 container_spec_cpu_quota{namespace="sample-app"} * 100) 
                 > 80
              for: 5m
              labels:
                severity: warning
                service: sample-app
              annotations:
                summary: "High CPU usage"
                description: "Pod {{ $labels.pod }} CPU usage is {{ $value }}% (threshold: 80%)"

        - name: database-health
          interval: 30s
          rules:
            # Alert: Database Connection Failure
            - alert: DatabaseConnectionFailure
              expr: |
                sum(rate(app_database_connection_errors_total[5m])) > 0
              for: 2m
              labels:
                severity: critical
                service: database
              annotations:
                summary: "Database connection failures"
                description: "Database connection errors detected: {{ $value }} errors/min"

        - name: redis-health
          interval: 30s
          rules:
            # Alert: Redis Connection Failure
            - alert: RedisConnectionFailure
              expr: |
                sum(rate(app_redis_connection_errors_total[5m])) > 0
              for: 2m
              labels:
                severity: warning
                service: redis
              annotations:
                summary: "Redis connection failures"
                description: "Redis connection errors detected: {{ $value }} errors/min"
      EOF
  }
}

# Note: Prometheus deployment is updated in monitoring.tf to mount alert rules
# This file only contains the alert rules ConfigMap
