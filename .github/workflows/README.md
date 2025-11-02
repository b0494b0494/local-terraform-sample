# GitHub Actions Workflows

## ?? Important Notes

### CI Workflow (`ci.yml`)
- **Automatically runs** on push/PR to `main` or `develop`
- Safe to push - only runs tests and builds
- No external dependencies or secrets required
- Runs in GitHub's free tier

### CD Workflow (`cd.yml`)
- **Configured to run** on push to `main`, but will **fail safely** if:
  - Kubernetes cluster is not accessible
  - kubectl is not configured
  - Terraform cannot connect to cluster
- **Safe to push** - workflow will skip deployment if cluster unavailable
- For actual deployments, you need:
  - Kubernetes cluster access
  - kubectl configuration (via secrets or manual setup)

## Running Workflows

### Disable Automatic CD

If you don't want CD to run automatically, edit `cd.yml`:

```yaml
on:
  # Remove 'push' to disable automatic deployment
  workflow_dispatch:  # Manual only
```

### Disable All Workflows

To disable GitHub Actions completely:
1. Delete `.github/workflows/` directory, or
2. Rename files to `.yml.disabled`

## Safety Features

? **No secrets in code** - All secrets must be configured in GitHub Secrets  
? **Fail-safe CD** - CD workflow fails gracefully if cluster unavailable  
? **Continue-on-error** - Deployment verification doesn't break workflow  
? **Local practice only** - Designed for local emulator environments  

## What Happens When You Push

1. **CI runs automatically**:
   - ? Tests run (safe, no external access)
   - ? Docker builds (safe, local build)
   - ? Terraform validates (safe, no apply)

2. **CD may run** (if configured):
   - ?? Will try to deploy
   - ?? Will fail if no cluster access (safe failure)
   - ? Won't break anything

## For Practice Environment

**Recommended**: Keep workflows for learning, but understand:
- CI will run automatically (safe)
- CD will attempt but fail safely (safe)
- No costs incurred if workflows fail
- No secrets exposed

## Disabling Workflows (Optional)

If you don't want GitHub Actions to run at all:

```bash
# Rename workflows directory
mv .github/workflows .github/workflows.disabled

# Or add to .gitignore (but won't commit workflows)
echo ".github/workflows/" >> .gitignore
```
