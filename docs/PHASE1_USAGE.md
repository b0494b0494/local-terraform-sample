# Phase 1 Features Usage Guide

This guide explains how to use the newly added Phase 1 features: Secrets, Variables, and Ingress.

## 1. Using Variables

### Basic Usage

Variables allow you to customize your deployment without changing code.

```bash
# Use default values
terraform apply

# Override variables via command line
terraform apply -var="replica_count=3" -var="environment=staging"

# Use a tfvars file
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform apply
```

### Available Variables

- `environment`: Environment name (dev, staging, prod)
- `app_name`: Application name
- `app_version`: Application version
- `replica_count`: Number of pod replicas
- `cpu_request`, `cpu_limit`: CPU resources
- `memory_request`, `memory_limit`: Memory resources
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `enable_ingress`: Enable Ingress resource
- `ingress_host`: Ingress hostname

### Example: Different Environments

```bash
# Development
terraform apply -var-file="terraform.tfvars.dev"

# Production
terraform apply -var-file="terraform.tfvars.prod"
```

## 2. Using Secrets

### Current Implementation

Secrets are defined in `secrets.tf`. **Important**: The current implementation uses hardcoded values for demo purposes only!

### How It Works

1. Secrets are created in Kubernetes
2. Deployment references secrets via `secret_key_ref`
3. Secrets are base64 encoded automatically

### Viewing Secrets

```bash
# List secrets
kubectl get secrets -n sample-app

# View secret (encoded)
kubectl get secret app-secret -n sample-app -o yaml

# Decode a secret value
kubectl get secret app-secret -n sample-app -o jsonpath='{.data.api_key}' | base64 -d
```

### Best Practices (For Production)

?? **Never hardcode secrets in Terraform!** Instead:

1. Use external secret management (Vault, AWS Secrets Manager)
2. Use Terraform data sources to fetch secrets
3. Use Kubernetes External Secrets Operator
4. Use sealed-secrets for GitOps workflows

### Example: Using External Secrets

```hcl
# This is just an example - not implemented yet
data "vault_generic_secret" "app_secret" {
  path = "secret/app"
}

resource "kubernetes_secret" "app_secret" {
  data = {
    api_key = data.vault_generic_secret.app_secret.data["api_key"]
  }
}
```

## 3. Using Ingress

### Enable Ingress

```bash
# Enable Ingress during apply
terraform apply -var="enable_ingress=true" -var="ingress_host=myapp.local"

# Or set in terraform.tfvars
echo 'enable_ingress = true' >> terraform.tfvars
echo 'ingress_host = "myapp.local"' >> terraform.tfvars
terraform apply
```

### Prerequisites

For Minikube:
```bash
minikube addons enable ingress
```

For kind:
```bash
# Install NGINX Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

### Access via Ingress

```bash
# Add to /etc/hosts (or C:\Windows\System32\drivers\etc\hosts on Windows)
# Get ingress IP first
kubectl get ingress -n sample-app
# Then add: <INGRESS_IP> myapp.local

# Access the app
curl http://myapp.local
```

### SSL/TLS (Future)

When ready for SSL:
1. Install cert-manager
2. Create ClusterIssuer
3. Uncomment TLS section in `ingress.tf`
4. Apply with certificate configuration

## Quick Examples

### Example 1: Scale to 3 replicas

```bash
terraform apply -var="replica_count=3"
```

### Example 2: Deploy to staging environment

```bash
terraform apply \
  -var="environment=staging" \
  -var="replica_count=3" \
  -var="log_level=DEBUG"
```

### Example 3: Enable Ingress with custom host

```bash
terraform apply \
  -var="enable_ingress=true" \
  -var="ingress_host=staging.example.com"
```

### Example 4: Production-like setup

```bash
# Create production tfvars
cat > terraform.tfvars <<EOF
environment = "prod"
replica_count = 5
cpu_request = "200m"
cpu_limit = "500m"
memory_request = "256Mi"
memory_limit = "512Mi"
log_level = "INFO"
enable_ingress = true
ingress_host = "api.example.com"
EOF

terraform apply
```

## Verification

After applying, verify everything:

```bash
# Check namespace
kubectl get namespace

# Check resources
kubectl get all -n <app-name>

# Check ConfigMap
kubectl get configmap -n <app-name>

# Check Secrets (encoded)
kubectl get secret -n <app-name>

# Check Ingress (if enabled)
kubectl get ingress -n <app-name>

# Check environment variables in pod
kubectl exec -n <app-name> <pod-name> -- env | grep -E "(APP_|API_|LOG_)"
```

## Next Steps

- Phase 2: HPA (Horizontal Pod Autoscaler)
- Phase 2: Persistent Volumes
- Phase 2: ServiceAccount & RBAC

See [ROADMAP.md](./ROADMAP.md) for full plan.
