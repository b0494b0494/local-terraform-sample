# CI/CD Guide

This guide explains the GitHub Actions CI/CD workflows.

## Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

Runs on every push and pull request:

**Jobs**:
- **test**: Run Python tests and linting
- **build**: Build and test Docker image
- **terraform-validate**: Validate Terraform configuration

**Triggers**:
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

### 2. CD Workflow (`.github/workflows/cd.yml`)

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

## Next Steps

- Add automated testing with coverage
- Add security scanning
- Add automated rollback
- Add blue-green deployments
- Add canary deployments
