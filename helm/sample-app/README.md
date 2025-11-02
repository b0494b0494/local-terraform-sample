# Sample App Helm Chart

This Helm chart provides a Kubernetes deployment for the sample-app application, converted from Terraform configuration.

## Installation

```bash
# Install chart
helm install sample-app ./helm/sample-app

# Install with custom values
helm install sample-app ./helm/sample-app -f my-values.yaml

# Upgrade existing release
helm upgrade sample-app ./helm/sample-app
```

## Uninstallation

```bash
helm uninstall sample-app
```

## Configuration

The following table lists configurable parameters and their default values:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `app.name` | Application name | `sample-app` |
| `app.version` | Application version | `1.0.0` |
| `app.environment` | Environment name | `dev` |
| `deployment.replicaCount` | Number of replicas | `2` |
| `deployment.image.repository` | Image repository | `sample-app` |
| `deployment.image.tag` | Image tag | `latest` |
| `resources.requests.cpu` | CPU request | `100m` |
| `resources.requests.memory` | Memory request | `128Mi` |
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `features.enableRedis` | Enable Redis | `true` |
| `features.enableDatabase` | Enable Database | `false` |
| `features.enableIngress` | Enable Ingress | `false` |
| `features.enableHPA` | Enable HPA | `false` |
| `features.enableRBAC` | Enable RBAC | `true` |

## Examples

### Basic Installation

```bash
helm install sample-app ./helm/sample-app
```

### With Redis and Database

```bash
cat > custom-values.yaml <<EOF
features:
  enableRedis: true
  enableDatabase: true
database:
  enabled: true
EOF

helm install sample-app ./helm/sample-app -f custom-values.yaml
```

### Production Configuration

```bash
cat > prod-values.yaml <<EOF
app:
  environment: production
deployment:
  replicaCount: 3
  image:
    tag: v1.0.0
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 1Gi
features:
  enableIngress: true
  enableHPA: true
  enablePrometheus: true
ingress:
  host: sample-app.example.com
EOF

helm install sample-app ./helm/sample-app -f prod-values.yaml
```

## Comparison with Terraform

This Helm chart provides similar functionality to the Terraform configuration:

- ? Namespace management
- ? ConfigMap and Secrets
- ? Deployment with health checks
- ? Service (ClusterIP/LoadBalancer)
- ? RBAC (ServiceAccount, Role, RoleBinding)
- ? Ingress
- ?? Some advanced features (HPA, Network Policies) are planned

## Migration from Terraform

To migrate from Terraform to Helm:

1. Export current values from Terraform outputs
2. Map Terraform variables to Helm values
3. Install Helm chart with converted values
4. Verify deployment
5. Remove Terraform resources (after validation)

## Notes

- This chart is simplified for learning purposes
- Production deployments may require additional configurations
- Review and adjust resource limits based on your needs
