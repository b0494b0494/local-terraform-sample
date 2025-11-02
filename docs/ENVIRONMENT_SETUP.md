# Environment Setup Guide

This guide helps you set up your local practice environment step by step.

## Prerequisites Installation

### 1. Docker & Docker Compose

**Linux (Ubuntu/Debian)**:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify
docker --version
docker compose version
```

**macOS**:
```bash
# Using Homebrew
brew install docker docker-compose

# Or download Docker Desktop
# https://www.docker.com/products/docker-desktop
```

### 2. Terraform

```bash
# Using package manager
# Ubuntu/Debian:
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform

# macOS (Homebrew):
brew install terraform

# Verify
terraform version
```

### 3. Kubernetes Emulator

Choose one:

#### Option A: Minikube (Recommended for beginners)

```bash
# Install Minikube
# Linux:
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# macOS:
brew install minikube

# Start Minikube
minikube start

# Verify
kubectl get nodes
```

#### Option B: kind

```bash
# Install kind
# Linux:
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# macOS:
brew install kind

# Create cluster
kind create cluster --name practice

# Verify
kubectl cluster-info --context kind-practice
```

#### Option C: k3d

```bash
# Install k3d
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

# Create cluster
k3d cluster create practice

# Verify
kubectl cluster-info
```

### 4. kubectl

```bash
# Linux:
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# macOS:
brew install kubectl

# Verify
kubectl version --client
```

## Initial Setup Checklist

### First Time Setup

- [ ] Install Docker & Docker Compose
- [ ] Install Terraform
- [ ] Install kubectl
- [ ] Install Kubernetes emulator (Minikube/kind/k3d)
- [ ] Start Kubernetes cluster
- [ ] Verify cluster access: `kubectl get nodes`
- [ ] Clone this repository
- [ ] Review README.md

### Application Setup

- [ ] Start Docker Compose: `make docker-compose-up`
- [ ] Verify app: `curl http://localhost:8080/health`
- [ ] Test LLM app: `curl -X POST http://localhost:8081/chat -d '{"message":"test"}'`

### Kubernetes Setup

- [ ] Build Docker image in K8s context
- [ ] Run `terraform init`
- [ ] Review `terraform plan`
- [ ] Apply: `terraform apply`

### Observability Setup (Optional)

- [ ] Enable Prometheus: `terraform apply -var="enable_prometheus=true"`
- [ ] Enable Grafana: `terraform apply -var="enable_grafana=true"`
- [ ] Access Prometheus: `kubectl port-forward -n monitoring svc/prometheus 9090:9090`
- [ ] Access Grafana: `kubectl port-forward -n monitoring svc/grafana 3000:3000`

## Environment Variables Summary

### Application Environment Variables

| Variable | Default | Description |
|---------|---------|-------------|
| `ENVIRONMENT` | `local` | Environment name (local, development, staging, production) |
| `PORT` | `8080` | Application port |
| `DEBUG` | `False` | Debug mode (set True for development only) |
| `APP_NAME` | `sample-app` | Application name |
| `APP_VERSION` | `1.0.0` | Application version |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `DATABASE_HOST` | - | PostgreSQL host (optional) |
| `DATABASE_PORT` | `5432` | PostgreSQL port |
| `DATABASE_NAME` | - | Database name |
| `DATABASE_USER` | - | Database user |
| `DATABASE_PASSWORD` | - | Database password |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_TTL` | `300` | Cache TTL in seconds |
| `JWT_SECRET` | - | JWT secret key (auto-generated if not set) |
| `JWT_EXPIRATION_HOURS` | `24` | JWT token expiration hours |

### Terraform Variables

See `variables.tf` for all available variables. Main ones:

| Variable | Default | Description |
|---------|---------|-------------|
| `environment` | `dev` | Environment name |
| `replica_count` | `2` | Number of pod replicas |
| `enable_prometheus` | `false` | Enable Prometheus |
| `enable_grafana` | `false` | Enable Grafana |
| `enable_loki` | `false` | Enable Loki |
| `enable_ingress` | `false` | Enable Ingress |
| `enable_hpa` | `true` | Enable HPA |

## Quick Setup Commands

```bash
# Complete setup in one go
minikube start && \
eval $(minikube docker-env) && \
docker build -t sample-app:latest . && \
terraform init && \
terraform apply
```

## Verification Commands

```bash
# Verify Docker
docker ps
docker-compose ps

# Verify Kubernetes
kubectl cluster-info
kubectl get nodes

# Verify Terraform
terraform version
terraform validate

# Verify Application
curl http://localhost:8080/health
curl http://localhost:8081/health

# Verify Kubernetes Deployment
kubectl get all -n sample-app
```

## Troubleshooting Setup

### Docker Issues

```bash
# Docker daemon not running
sudo systemctl start docker  # Linux
# Or start Docker Desktop (macOS/Windows)

# Permission denied
sudo usermod -aG docker $USER
# Log out and back in
```

### Kubernetes Issues

```bash
# Minikube not starting
minikube delete
minikube start --driver=docker

# kubectl connection refused
kubectl config get-contexts
kubectl config use-context <context-name>
```

### Terraform Issues

```bash
# Provider download failed
terraform init -upgrade

# Validation errors
terraform fmt
terraform validate
```

## Next Steps

After setup:
1. Review [ARCHITECTURE.md](./ARCHITECTURE.md)
2. Start with [PRACTICE.md](./PRACTICE.md) exercises
3. Refer to [QUICKREF.md](./QUICKREF.md) for commands
4. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) if issues arise
