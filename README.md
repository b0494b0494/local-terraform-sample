# Local Terraform Practice Sample App

A simple sample application for practicing Terraform and Kubernetes in a local emulator environment.

## Prerequisites

- Docker & Docker Compose
- Terraform >= 1.0
- Kubernetes (Minikube/kind/k3d) + kubectl

## Quick Start

### 1. Start the App (Easiest Way)

```bash
make docker-compose-up
# or
docker-compose up -d
```

Access: `http://localhost:8080`

### 2. Start LLM Observability App

```bash
docker-compose up llm-app -d
```

Access: `http://localhost:8081`

**Observability Features**:
- Structured logging (JSON format)
- Prometheus format metrics (`/metrics`)
- Distributed tracing (`/traces`)
- APM performance stats (`/apm/stats`)
- Dashboard (open `observability_dashboard.html` in browser)

### 3. Deploy to Kubernetes with Terraform

```bash
# Prepare Kubernetes environment (Minikube example)
minikube start
eval $(minikube docker-env)
docker build -t sample-app:latest .

# Deploy with Terraform
terraform init
terraform apply

# Verify
kubectl get all -n sample-app
kubectl port-forward -n sample-app svc/sample-app-service 8080:80
```

### 4. Deploy with Helm (Alternative)

```bash
# Install Helm chart
helm install sample-app ./helm/sample-app

# Install with custom values
helm install sample-app ./helm/sample-app -f my-values.yaml

# Upgrade
helm upgrade sample-app ./helm/sample-app
```

### 5. Blue-Green Deployment

```bash
# Enable blue-green deployment
terraform apply -var="enable_blue_green=true" -var="active_environment=blue"

# Switch to green
./scripts/blue-green-switch.sh

# Rollback if needed
./scripts/blue-green-rollback.sh
```

### 6. Cleanup

```bash
terraform destroy
docker-compose down
```

## Useful Commands

```bash
make help              # List all commands
make docker-compose-up # Start app
make terraform-init    # Initialize Terraform
make terraform-apply   # Deploy with Terraform
make test             # Run tests
```

## Learning Resources

- **[docs/LEARNING_PATH.md](./docs/LEARNING_PATH.md)** - Structured learning path (start here!)
- **[docs/TASKS.md](./docs/TASKS.md)** - Incremental practice tasks (gradually add features!)
- **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - System architecture and diagrams
- **[docs/ENVIRONMENT_SETUP.md](./docs/ENVIRONMENT_SETUP.md)** - Complete setup guide
- **[docs/PRACTICE.md](./docs/PRACTICE.md)** - Practice exercises (beginner to advanced)
- **[docs/QUICKREF.md](./docs/QUICKREF.md)** - Quick reference (common commands)
- **[docs/TESTING.md](./docs/TESTING.md)** - Testing guide (how to test features)
- **[docs/TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)** - Troubleshooting guide

### Feature-Specific Guides

- **[docs/HPA_GUIDE.md](./docs/HPA_GUIDE.md)** - Horizontal Pod Autoscaler
- **[docs/STORAGE_GUIDE.md](./docs/STORAGE_GUIDE.md)** - Persistent Volumes
- **[docs/RBAC_GUIDE.md](./docs/RBAC_GUIDE.md)** - ServiceAccount & RBAC
- **[docs/NETWORK_POLICIES_GUIDE.md](./docs/NETWORK_POLICIES_GUIDE.md)** - Network Policies (security)
- **[docs/INIT_CONTAINERS_GUIDE.md](./docs/INIT_CONTAINERS_GUIDE.md)** - Init Containers (dependency management)
- **[docs/DATABASE_GUIDE.md](./docs/DATABASE_GUIDE.md)** - PostgreSQL database integration
- **[docs/SIDECAR_GUIDE.md](./docs/SIDECAR_GUIDE.md)** - Sidecar pattern (multi-container pods)
- **[docs/AUTH_GUIDE.md](./docs/AUTH_GUIDE.md)** - API Authentication & Authorization
- **[docs/JOBS_GUIDE.md](./docs/JOBS_GUIDE.md)** - Jobs and CronJobs (task scheduling)
- **[docs/PROMETHEUS_GUIDE.md](./docs/PROMETHEUS_GUIDE.md)** - Prometheus monitoring
- **[docs/GRAFANA_GUIDE.md](./docs/GRAFANA_GUIDE.md)** - Grafana dashboards
- **[docs/LOKI_GUIDE.md](./docs/LOKI_GUIDE.md)** - Loki log aggregation
- **[docs/CICD_GUIDE.md](./docs/CICD_GUIDE.md)** - CI/CD workflows
- **[docs/BLUE_GREEN_GUIDE.md](./docs/BLUE_GREEN_GUIDE.md)** - Blue-Green Deployment strategy

## LLM Observability Practice

Practice observability (monitoring, logging, tracing) for LLM applications locally.

### Features

1. **Structured Logging**: JSON format log output
2. **Metrics**: Prometheus format metrics (request count, response time, tokens, etc.)
3. **Tracing**: Simple distributed tracing (OpenTelemetry-style)
4. **Dashboard**: HTML-based simple dashboard

### Usage

```bash
# Start LLM app
docker-compose up llm-app -d

# Test chat API
curl -X POST http://localhost:8081/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# Check metrics
curl http://localhost:8081/metrics

# Check tracing data
curl http://localhost:8081/traces

# Open dashboard (in browser)
open observability_dashboard.html
```

## Security Notice

⚠️ **For local practice environment only. Do not use in production.**

- `DEBUG=True` is for development only
- Do not include secrets in code (excluded in `.gitignore`)

## Recent Features

### Phase 3: Production Readiness ✅
- **Advanced Observability**: Prometheus alerting rules, distributed tracing, APM hooks
- **API Authentication**: JWT tokens, API keys, RBAC, rate limiting
- **Blue-Green Deployment**: Zero-downtime deployments with rollback support

### Phase 4: CI/CD & Helm ✅
- **Helm Chart**: Complete Terraform to Helm conversion
- **Advanced CI/CD**: Security scanning, multi-stage builds, automated testing

## File Structure

```
app.py                      # Flask app (with auth, metrics, tracing)
llm_app.py                  # LLM-style app (with observability)
auth.py                     # Authentication module
observability_dashboard.html # Observability dashboard
docker-compose.yml          # Docker Compose configuration
main.tf                     # Terraform configuration (standard deployment)
deployment_strategy.tf      # Blue-Green deployment strategy
alerting_rules.tf           # Prometheus alerting rules
modules/blue-green/         # Blue-Green deployment module
helm/sample-app/            # Helm chart
tests/                      # Test suites
scripts/                    # Helper scripts
docs/                       # Documentation
  LEARNING_PATH.md          # Learning path (start here)
  ARCHITECTURE.md           # System architecture
  ENVIRONMENT_SETUP.md      # Setup guide
  PRACTICE.md               # Practice exercises
  QUICKREF.md               # Quick reference
  TROUBLESHOOTING.md        # Troubleshooting
  BLUE_GREEN_GUIDE.md       # Blue-Green deployment guide
  [Feature guides]          # HPA, Storage, RBAC, Monitoring, etc.
.github/workflows/         # CI/CD workflows
  ci.yml                    # Basic CI
  advanced-ci.yml           # Advanced CI/CD pipeline
.cursorrules               # Cursor rules (security)
```

See [Learning Resources](#learning-resources) section for all documentation.
