#!/bin/bash
# Blue-Green Deployment Rollback Script
# Quickly rollback to the previous environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Get current active environment
CURRENT_ENV=$(terraform output -raw active_environment 2>/dev/null || echo "blue")
ROLLBACK_ENV=""

if [ "$CURRENT_ENV" = "blue" ]; then
    ROLLBACK_ENV="green"
else
    ROLLBACK_ENV="blue"
fi

echo "=== Blue-Green Deployment Rollback ==="
echo "Current active environment: $CURRENT_ENV"
echo "Rolling back to: $ROLLBACK_ENV"
echo ""

# Confirm
read -p "Are you sure you want to rollback to $ROLLBACK_ENV? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Rollback cancelled."
    exit 1
fi

# Check if blue-green is enabled
if ! terraform output -raw blue_green_enabled 2>/dev/null | grep -q "true"; then
    echo "Error: Blue-green deployment is not enabled."
    exit 1
fi

# Apply terraform with rollback environment
echo "Rolling back to $ROLLBACK_ENV environment..."
terraform apply -var="active_environment=$ROLLBACK_ENV" -auto-approve

echo ""
echo "? Rollback complete. Traffic now routed to $ROLLBACK_ENV environment"
echo ""
echo "To verify deployment status:"
echo "  kubectl get pods -n sample-app -l environment=$ROLLBACK_ENV"
echo "  kubectl get svc -n sample-app sample-app-main"
