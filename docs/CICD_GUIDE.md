# CI/CD Guide

This guide explains the GitHub Actions CI/CD workflows.

## Workflows

### 1. Basic CI Workflow (`.github/workflows/ci.yml`)

Runs on every push and pull request:

**Jobs**:
- **test**: Run Python tests and linting
- **build**: Build and test Docker image
- **terraform-validate**: Validate Terraform configuration

**Triggers**:
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

### 2. Advanced CI Workflow (`.github/workflows/advanced-ci.yml`)

Enhanced CI pipeline with security, quality gates, and comprehensive testing:

**Jobs**:
- **security-scan**: Trivy vulnerability scanning (filesystem and Docker images)
- **lint**: Code quality checks (flake8, black, isort)
- **docker-build**: Multi-stage Docker build with caching and image scanning
- **unit-tests**: Unit tests with coverage reporting
- **integration-tests**: Docker Compose integration tests
- **terraform-validate**: Terraform format, init, validate, plan
- **performance-tests**: Basic load testing (main branch only)
- **ci-summary**: Summary of all job results

**Features**:
- Security scanning with GitHub Security integration
- Code quality enforcement
- Docker layer caching
- Test coverage reporting (Codecov)
- Performance testing
- Comprehensive validation

**Triggers**:
- Push to `main` or `develop`
- Pull requests to `main` or `develop`
- Manual dispatch (workflow_dispatch)

### 3. CD Workflow (`.github/workflows/cd.yml`)

Deploys to Kubernetes (manual or automatic):

**Steps**:
1. Setup kubectl and Terraform
2. Configure Kubernetes connection
3. Terraform plan and apply
4. Verify deployment

**Triggers**:
- Push to `main` (automatic)
- Manual dispatch (workflow_dispatch)

## Using CI/CD

### Automatic CI

CI runs automatically on push:

```bash
git push origin main
# CI workflow will run automatically
```

### Manual CD Deployment

```bash
# Via GitHub UI:
# 1. Go to Actions tab
# 2. Select "CD - Deploy to Kubernetes"
# 3. Click "Run workflow"

# Or via GitHub CLI:
gh workflow run cd.yml
```

## Configuration

### For Local Testing

CI/CD workflows are configured for GitHub Actions. For local practice:

1. **CI**: Can run locally:
   ```bash
   # Test locally
   python test_app.py
   
   # Build Docker
   docker build -t sample-app:test .
   
   # Validate Terraform
   terraform init
   terraform validate
   ```

2. **CD**: Requires:
   - Kubernetes cluster access
   - kubectl configured
   - Terraform access to cluster

### For Production

Update workflows with:

1. **Secrets**: Store kubeconfig or service account keys
2. **Environments**: Separate dev/staging/prod
3. **Approvals**: Manual approval gates
4. **Notifications**: Slack/email on failures

## Workflow Customization

### Add More Tests

Edit `.github/workflows/ci.yml`:

```yaml
- name: Run integration tests
  run: |
    docker-compose up -d
    sleep 10
    python test_app.py
    docker-compose down
```

### Add Security Scanning

```yaml
- name: Security scan
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    scan-ref: '.'
```

### Add Terraform Plan Review

```yaml
- name: Terraform Plan
  run: terraform plan -out=tfplan
  
- name: Comment PR
  uses: actions/github-script@v6
  with:
    script: |
      // Post plan output as PR comment
```

## Best Practices

1. **Fail Fast**: Run fast tests first
2. **Parallel Jobs**: Run independent jobs in parallel
3. **Cache Dependencies**: Cache pip packages, Docker layers
4. **Artifacts**: Save build artifacts for debugging
5. **Notifications**: Alert on failures

## Troubleshooting

### CI Failing

```bash
# Run tests locally first
python test_app.py

# Check Docker build
docker build -t test .

# Validate Terraform
terraform validate
```

### CD Not Deploying

1. Check Kubernetes access
2. Verify secrets are configured
3. Check workflow permissions
4. Review workflow logs

## Advanced CI Features

### Security Scanning

The Advanced CI pipeline includes Trivy for vulnerability scanning:

- **Filesystem Scan**: Scans all files for known vulnerabilities
- **Docker Image Scan**: Scans built Docker images
- **Results**: Uploaded to GitHub Security tab for review

### Code Quality

Enforced code quality checks:

- **flake8**: Linting for Python code
- **black**: Code formatting (checked, not auto-fixed)
- **isort**: Import statement sorting

### Docker Build Optimization

- **Multi-stage builds**: Optimized for size and security
- **Layer caching**: GitHub Actions cache for faster builds
- **Image scanning**: Each built image is scanned for vulnerabilities

### Testing

- **Unit Tests**: pytest with coverage reporting
- **Integration Tests**: Full Docker Compose stack testing
- **Performance Tests**: Basic load testing (on main branch)

### CI Summary

All job results are summarized in the workflow run, making it easy to see which checks passed or failed.

## Choosing CI Workflows

- **Basic CI** (`ci.yml`): Quick, lightweight checks for rapid feedback
- **Advanced CI** (`advanced-ci.yml`): Comprehensive checks with security and quality gates

Use Advanced CI for:
- Production-ready code
- Pull requests requiring thorough review
- Security-sensitive deployments

## Next Steps

- ? Automated testing with coverage (implemented)
- ? Security scanning (implemented)
- ? Multi-stage builds (implemented)
- ? Blue-green deployments (implemented)
- Future: Automated rollback on health check failures
- Future: Canary deployments
- Future: GitOps integration (ArgoCD/Flux)
