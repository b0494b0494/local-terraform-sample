# Jobs and CronJobs Guide

This guide explains how to use Kubernetes Jobs and CronJobs for one-time and scheduled tasks.

## Overview

**Jobs**: Run to completion (one-time tasks)  
**CronJobs**: Run on a schedule (recurring tasks)

## Jobs vs CronJobs

| Feature | Job | CronJob |
|---------|-----|---------|
| **Execution** | Once, to completion | Scheduled, recurring |
| **Use case** | Manual tasks, one-off | Automated maintenance |
| **Completion** | Deleted after TTL | Keeps history |
| **Trigger** | Manual or programmatic | Cron schedule |

## Jobs in This Project

### 1. cleanup-logs Job

**Type**: One-time Job  
**Purpose**: Cleanup old log files

**When to use**:
- Manual cleanup operations
- One-off maintenance tasks
- Ad-hoc operations

**Configuration**:
```hcl
resource "kubernetes_job" "cleanup_logs" {
  spec {
    ttl_seconds_after_finished = 86400  # Deleted after 24 hours
    
    template {
      spec {
        restart_policy = "OnFailure"  # Retry on failure
        # ... container definition ...
      }
    }
  }
}
```

**Run manually**:
```bash
# Job is created by Terraform, but you can trigger it manually
kubectl create job --from=cronjob/sample-app-daily-log-rotation cleanup-manual -n sample-app

# Or create a one-time job from the CronJob template
kubectl run cleanup-manual --image=busybox:1.36 --restart=Never --rm -it -- sh -c "echo cleanup"
```

## CronJobs in This Project

### 1. daily-log-rotation

**Schedule**: Daily at 2:00 AM UTC (configurable)  
**Purpose**: Rotate and archive old logs

**Configuration**:
```hcl
resource "kubernetes_cron_job" "daily_log_rotation" {
  spec {
    schedule = "0 2 * * *"  # Daily at 2 AM
    time_zone = "UTC"
    
    # Keep history
    successful_jobs_history_limit = 3
    failed_jobs_history_limit    = 1
    
    # Must start within 5 minutes of schedule
    starting_deadline_seconds = 300
  }
}
```

### 2. health-check-report

**Schedule**: Every hour at minute 0  
**Purpose**: Generate health check reports

**Schedule**: `0 * * * *` (every hour)

## Cron Schedule Format

```
?????????????? minute (0 - 59)
? ?????????????? hour (0 - 23)
? ? ?????????????? day of month (1 - 31)
? ? ? ?????????????? month (1 - 12)
? ? ? ? ?????????????? day of week (0 - 6) (Sunday to Saturday)
? ? ? ? ?
* * * * *
```

**Examples**:
- `0 2 * * *` - Daily at 2:00 AM
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 0` - Every Sunday at midnight
- `*/15 * * * *` - Every 15 minutes
- `0 9-17 * * 1-5` - Every hour 9 AM to 5 PM, Monday to Friday

## Usage

### Enable Jobs and CronJobs

```bash
# Via terraform.tfvars
enable_jobs = true
enable_cronjobs = true
cronjob_schedule = "0 2 * * *"  # Daily at 2 AM

# Or via command line
terraform apply \
  -var="enable_jobs=true" \
  -var="enable_cronjobs=true" \
  -var="cronjob_schedule=0 2 * * *"
```

### View Jobs

```bash
# List all jobs
kubectl get jobs -n sample-app

# Describe a job
kubectl describe job sample-app-cleanup-logs -n sample-app

# View job logs
kubectl logs job/sample-app-cleanup-logs -n sample-app
```

### View CronJobs

```bash
# List all cronjobs
kubectl get cronjobs -n sample-app

# Describe a cronjob
kubectl describe cronjob sample-app-daily-log-rotation -n sample-app

# View cronjob schedule
kubectl get cronjob sample-app-daily-log-rotation -n sample-app -o yaml
```

### View Job History

```bash
# List job instances created by CronJob
kubectl get jobs -n sample-app -l job-type=maintenance

# View logs from a specific job run
kubectl logs job/sample-app-daily-log-rotation-1234567890 -n sample-app
```

### Manually Trigger a CronJob

```bash
# Create a one-time job from a CronJob
kubectl create job --from=cronjob/sample-app-daily-log-rotation \
  manual-log-rotation-$(date +%s) -n sample-app
```

## Job Lifecycle

### Job States

1. **Pending**: Job created, waiting for pod to start
2. **Running**: Pod is running
3. **Succeeded**: Job completed successfully
4. **Failed**: Job failed (will retry if restart_policy=OnFailure)

### CronJob Lifecycle

1. **Scheduled**: CronJob exists, waiting for schedule
2. **Creating**: Job created at scheduled time
3. **Running**: Job pod is running
4. **Completed**: Job finished, kept in history
5. **Cleaned up**: Old jobs deleted after TTL

## Monitoring

### Check Job Status

```bash
# Get job status
kubectl get job sample-app-cleanup-logs -n sample-app -o jsonpath='{.status}'

# Check completion
kubectl get job sample-app-cleanup-logs -n sample-app \
  -o jsonpath='{.status.conditions[*].type}'
```

### Check CronJob Status

```bash
# Last schedule time
kubectl get cronjob sample-app-daily-log-rotation -n sample-app \
  -o jsonpath='{.status.lastScheduleTime}'

# Active jobs
kubectl get cronjob sample-app-daily-log-rotation -n sample-app \
  -o jsonpath='{.status.active}'
```

## Troubleshooting

### Job Stuck in Pending

**Symptoms**: Job never starts

**Check**:
```bash
# Describe the job
kubectl describe job <job-name> -n sample-app

# Check pod status
kubectl get pods -n sample-app -l job-name=<job-name>

# Check events
kubectl get events -n sample-app --sort-by='.lastTimestamp'
```

**Common causes**:
- Resource quotas exceeded
- Node resources insufficient
- Image pull errors
- Network Policies blocking

### CronJob Not Running

**Symptoms**: CronJob exists but no jobs created

**Check**:
```bash
# Verify schedule
kubectl get cronjob <name> -n sample-app -o yaml | grep schedule

# Check for suspend flag
kubectl get cronjob <name> -n sample-app -o jsonpath='{.spec.suspend}'

# Check last schedule time
kubectl get cronjob <name> -n sample-app -o jsonpath='{.status.lastScheduleTime}'
```

**Solutions**:
- Verify cron schedule format
- Check if suspended (`spec.suspend=true`)
- Verify timezone settings
- Check controller logs

### Job Failing Repeatedly

**Symptoms**: Job keeps failing and retrying

**Check**:
```bash
# View job logs
kubectl logs job/<job-name> -n sample-app

# Check restart policy
kubectl get job <job-name> -n sample-app -o jsonpath='{.spec.template.spec.restartPolicy}'
```

**Solutions**:
- Fix the command/script error
- Change `restart_policy` to "Never" to stop retries
- Increase resource limits if OOMKilled
- Check dependencies (services, volumes)

## Best Practices

### 1. Resource Limits

Always set resource requests and limits:
```hcl
resources {
  requests = { cpu = "100m", memory = "128Mi" }
  limits   = { cpu = "500m", memory = "256Mi" }
}
```

### 2. TTL Management

Set appropriate TTL to prevent job accumulation:
```hcl
ttl_seconds_after_finished = 86400  # 24 hours
```

### 3. History Limits

Keep only necessary job history:
```hcl
successful_jobs_history_limit = 3
failed_jobs_history_limit    = 1
```

### 4. Starting Deadlines

Set realistic deadlines for scheduled jobs:
```hcl
starting_deadline_seconds = 300  # 5 minutes
```

### 5. Idempotent Operations

Make jobs idempotent (safe to rerun):
- Check if work already done
- Use atomic operations
- Handle partial failures gracefully

## Advanced Patterns

### Parallel Jobs

Run multiple jobs concurrently:

```hcl
resource "kubernetes_job" "parallel_task" {
  spec {
    parallelism = 3  # Run 3 pods in parallel
    completions = 10  # Total 10 completions needed
    # ...
  }
}
```

### Job Dependencies

Use init containers or separate jobs for dependencies:

```hcl
# Job 1: Prepare data
# Job 2: Process data (depends on Job 1)
```

### Backoff Strategy

Configure retry backoff:

```hcl
spec {
  backoff_limit = 3  # Maximum retries
  # ...
}
```

## Use Cases

### Maintenance Tasks
- Database cleanup
- Log rotation
- Cache invalidation
- Archive old data

### Reporting
- Daily reports
- Metrics aggregation
- Health checks
- Compliance reports

### Data Processing
- Batch processing
- ETL jobs
- Data synchronization
- Backup operations

## Next Steps

- Integrate with monitoring (Prometheus alerts on job failures)
- Add job dependencies
- Implement parallel job execution
- Create job templates for common patterns
