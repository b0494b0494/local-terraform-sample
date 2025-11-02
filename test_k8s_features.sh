#!/bin/bash
# Test script for Kubernetes features
# Tests: Init Containers, Jobs, CronJobs (if deployed)

set -e

NAMESPACE="${NAMESPACE:-sample-app}"
KUBECTL="${KUBECTL:-kubectl}"

echo "=========================================="
echo "Kubernetes Features Test"
echo "=========================================="
echo ""

# Check if kubectl is available
if ! command -v $KUBECTL &> /dev/null; then
    echo "? kubectl not found. Please install kubectl first."
    exit 1
fi

# Check namespace exists
echo "1. Checking namespace..."
if $KUBECTL get namespace "$NAMESPACE" &> /dev/null; then
    echo "   ? Namespace '$NAMESPACE' exists"
else
    echo "   ? Namespace '$NAMESPACE' not found"
    echo "   Deploy first with: terraform apply"
    exit 1
fi

# Test Init Containers
echo ""
echo "2. Testing Init Containers..."
POD_NAME=$($KUBECTL get pods -n "$NAMESPACE" -l app=sample-app -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -z "$POD_NAME" ]; then
    echo "   ??  No pods found. Deploy first with: terraform apply"
else
    echo "   Found pod: $POD_NAME"
    
    # Check init containers
    INIT_CONTAINERS=$($KUBECTL get pod "$POD_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.initContainers[*].name}' 2>/dev/null || echo "")
    
    if [ -n "$INIT_CONTAINERS" ]; then
        echo "   ? Init Containers found: $INIT_CONTAINERS"
        
        # Check init container status
        for INIT in $INIT_CONTAINERS; do
            STATUS=$($KUBECTL get pod "$POD_NAME" -n "$NAMESPACE" -o jsonpath="{.status.initContainerStatuses[?(@.name==\"$INIT\")].ready}" 2>/dev/null || echo "false")
            if [ "$STATUS" = "true" ]; then
                echo "   ? Init Container '$INIT': Completed"
            else
                echo "   ??  Init Container '$INIT': Not ready yet"
            fi
        done
        
        # Try to get init container logs
        FIRST_INIT=$(echo $INIT_CONTAINERS | cut -d' ' -f1)
        if [ -n "$FIRST_INIT" ]; then
            echo ""
            echo "   Init Container '$FIRST_INIT' logs (last 5 lines):"
            $KUBECTL logs "$POD_NAME" -n "$NAMESPACE" -c "$FIRST_INIT" --tail=5 2>/dev/null || echo "      (logs not available)"
        fi
    else
        echo "   ??  No Init Containers found (this is OK if disabled)"
    fi
fi

# Test Jobs (if enabled)
echo ""
echo "3. Testing Jobs..."
JOBS=$($KUBECTL get jobs -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")

if [ -n "$JOBS" ]; then
    echo "   ? Jobs found: $JOBS"
    for JOB in $JOBS; do
        STATUS=$($KUBECTL get job "$JOB" -n "$NAMESPACE" -o jsonpath='{.status.conditions[?(@.type=="Complete")].status}' 2>/dev/null || echo "Unknown")
        if [ "$STATUS" = "True" ]; then
            echo "   ? Job '$JOB': Completed"
        elif [ "$STATUS" = "False" ]; then
            echo "   ??  Job '$JOB': Failed"
        else
            echo "   ? Job '$JOB': Status unknown or pending"
        fi
    done
else
    echo "   ??  No Jobs found (enable with: terraform apply -var=\"enable_jobs=true\")"
fi

# Test CronJobs (if enabled)
echo ""
echo "4. Testing CronJobs..."
CRONJOBS=$($KUBECTL get cronjobs -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' 2>/dev/null || echo "")

if [ -n "$CRONJOBS" ]; then
    echo "   ? CronJobs found: $CRONJOBS"
    for CRONJOB in $CRONJOBS; do
        SCHEDULE=$($KUBECTL get cronjob "$CRONJOB" -n "$NAMESPACE" -o jsonpath='{.spec.schedule}' 2>/dev/null || echo "Unknown")
        SUSPENDED=$($KUBECTL get cronjob "$CRONJOB" -n "$NAMESPACE" -o jsonpath='{.spec.suspend}' 2>/dev/null || echo "false")
        LAST_SCHEDULE=$($KUBECTL get cronjob "$CRONJOB" -n "$NAMESPACE" -o jsonpath='{.status.lastScheduleTime}' 2>/dev/null || echo "Never")
        
        echo "   ?? CronJob '$CRONJOB':"
        echo "      Schedule: $SCHEDULE"
        echo "      Suspended: $SUSPENDED"
        echo "      Last Run: $LAST_SCHEDULE"
        
        # Check for active jobs from this cronjob
        ACTIVE_JOBS=$($KUBECTL get jobs -n "$NAMESPACE" -l job-name="$CRONJOB" --no-headers 2>/dev/null | wc -l || echo "0")
        echo "      Active Jobs: $ACTIVE_JOBS"
    done
else
    echo "   ??  No CronJobs found (enable with: terraform apply -var=\"enable_cronjobs=true\")"
fi

# Test Redis (if enabled)
echo ""
echo "5. Testing Redis..."
REDIS_POD=$($KUBECTL get pods -n "$NAMESPACE" -l app=sample-app-redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -n "$REDIS_POD" ]; then
    echo "   ? Redis pod found: $REDIS_POD"
    REDIS_STATUS=$($KUBECTL get pod "$REDIS_POD" -n "$NAMESPACE" -o jsonpath='{.status.phase}' 2>/dev/null || echo "Unknown")
    echo "   Status: $REDIS_STATUS"
    
    # Try to ping Redis
    if [ "$REDIS_STATUS" = "Running" ]; then
        if $KUBECTL exec -n "$NAMESPACE" "$REDIS_POD" -- redis-cli ping &> /dev/null; then
            echo "   ? Redis is responding"
        else
            echo "   ??  Redis pod running but not responding"
        fi
    fi
else
    echo "   ??  Redis not found (enable with: terraform apply -var=\"enable_redis=true\")"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "To view detailed pod information:"
echo "  kubectl describe pod $POD_NAME -n $NAMESPACE"
echo ""
echo "To view init container logs:"
echo "  kubectl logs $POD_NAME -n $NAMESPACE -c <init-container-name>"
echo ""
echo "To trigger a CronJob manually:"
echo "  kubectl create job --from=cronjob/<cronjob-name> manual-<name> -n $NAMESPACE"
