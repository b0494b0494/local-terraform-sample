#!/bin/bash
# Blue-Green Deployment Switch Script
# Switches traffic between blue and green environments

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Get current active environment
cd terraform
CURRENT_ENV=$(terraform output -raw active_environment 2>/dev/null || echo "blue")
cd ..
NEW_ENV=""

if [ "$CURRENT_ENV" = "blue" ]; then
    NEW_ENV="green"
else
    NEW_ENV="blue"
fi

echo "=== Blue-Green Deployment Switch ==="
echo "Current active environment: $CURRENT_ENV"
echo "Switching to: $NEW_ENV"
echo ""

# Confirm
read -p "Are you sure you want to switch traffic to $NEW_ENV? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Switch cancelled."
    exit 1
fi

# Check if blue-green is enabled
cd terraform
if ! terraform output -raw blue_green_enabled 2>/dev/null | grep -q "true"; then
    cd ..
    echo "Error: Blue-green deployment is not enabled."
    echo "Set enable_blue_green = true in terraform.tfvars"
    exit 1
fi

# Apply terraform with new active environment
echo "Updating active environment to $NEW_ENV..."
terraform apply -var="active_environment=$NEW_ENV" -auto-approve
cd ..

echo ""
echo "? Traffic switched to $NEW_ENV environment"
echo ""
echo "To verify:"
echo "  kubectl get pods -n sample-app -l environment=$NEW_ENV"
echo "  kubectl get svc -n sample-app sample-app-main"
