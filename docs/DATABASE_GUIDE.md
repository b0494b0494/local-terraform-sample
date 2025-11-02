# Database Guide

This guide explains how to use the PostgreSQL database integration.

## Overview

The project includes a PostgreSQL database deployment with automatic schema migration.

## Features

- **PostgreSQL 16** deployment in Kubernetes
- **Automatic migration** via Init Containers
- **Connection pooling** in application
- **Persistent storage** for data
- **Health checks** for readiness
- **Graceful degradation** (works without database)

## Architecture

```
App Pod
  ??? Init: wait-for-database (checks PostgreSQL ready)
  ??? Init: migrate-database (runs migration.py)
  ??? Main: sample-app (connects to database)
           ?
    PostgreSQL Service
           ?
    PostgreSQL Pod (Deployment)
           ?
    PersistentVolumeClaim (5Gi default)
```

## Usage

### Enable Database

```bash
# Via terraform.tfvars
enable_database = true

# Or via command line
terraform apply -var="enable_database=true"
```

### Custom Configuration

```hcl
enable_database = true
database_name = "myapp"
database_user = "appuser"
database_password = "secure_password"
database_storage_size = "10Gi"
```

## Database Schema

The migration script creates:

1. **users** table:
   - `id` (SERIAL PRIMARY KEY)
   - `username` (VARCHAR, UNIQUE)
   - `email` (VARCHAR, UNIQUE)
   - `created_at` (TIMESTAMP)
   - `updated_at` (TIMESTAMP with auto-update trigger)

2. **requests_log** table:
   - `id` (SERIAL PRIMARY KEY)
   - `endpoint` (VARCHAR)
   - `method` (VARCHAR)
   - `ip_address` (VARCHAR)
   - `user_agent` (TEXT)
   - `created_at` (TIMESTAMP)
   - Index on `created_at`

## Application Endpoints

### `/db/status`

Check database connection status:

```bash
curl http://localhost:8080/db/status
```

**Response**:
```json
{
  "status": "connected",
  "version": "PostgreSQL 16.0"
}
```

### `/db/query`

Execute a database query (for testing):

```bash
curl -X POST http://localhost:8080/db/query \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM users LIMIT 5;"}'
```

**Response**:
```json
{
  "status": "success",
  "results": [...]
}
```

### `/ready`

Readiness check includes database verification:

```bash
curl http://localhost:8080/ready
```

**Response** (with database):
```json
{
  "status": "ready",
  "service": "sample-app",
  "database_connected": true
}
```

## Manual Migration

### Run Migration Locally

```bash
# Set environment variables
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_NAME=sampleapp
export DATABASE_USER=appuser
export DATABASE_PASSWORD=demo_password_123

# Run migration
python migration.py
```

### Drop Schema (Testing)

```bash
python migration.py drop
# Confirmation required
```

## Connection Pooling

The application uses connection pooling:

- **Min connections**: 1
- **Max connections**: 5
- **Thread-safe**: Yes (ThreadedConnectionPool)

**Benefits**:
- Reduced connection overhead
- Better resource management
- Automatic connection reuse

## Troubleshooting

### Database Not Connecting

**Check database pod**:
```bash
kubectl get pods -n sample-app -l app=sample-app-postgresql
kubectl logs <postgresql-pod> -n sample-app
```

**Check init container logs**:
```bash
kubectl logs <app-pod> -n sample-app -c wait-for-database
kubectl logs <app-pod> -n sample-app -c migrate-database
```

**Verify credentials**:
```bash
kubectl get secret sample-app-db-credentials -n sample-app -o yaml
```

### Migration Failing

**Check migration logs**:
```bash
kubectl logs <app-pod> -n sample-app -c migrate-database
```

**Common issues**:
- Database not ready (check wait-for-database logs)
- Permission errors (verify Secret credentials)
- Schema already exists (migration is idempotent, safe to retry)

### Connection Pool Exhausted

**Symptoms**: `/db/query` returns connection errors

**Solutions**:
- Check active connections: `SELECT count(*) FROM pg_stat_activity;`
- Increase pool size in `app.py`
- Check for connection leaks (connections not returned to pool)

## Best Practices

### 1. Use Secrets for Credentials

Never hardcode passwords. Use Kubernetes Secrets:

```hcl
variable "database_password" {
  type      = string
  sensitive = true
}
```

### 2. Health Checks

Ensure health checks verify actual connectivity:

```hcl
readiness_probe {
  exec {
    command = ["pg_isready", "-U", var.database_user]
  }
}
```

### 3. Persistent Storage

Use PersistentVolumeClaims for data:

```hcl
resource "kubernetes_persistent_volume_claim" "postgresql_data" {
  spec {
    access_modes = ["ReadWriteOnce"]
    resources {
      requests = { storage = "5Gi" }
    }
  }
}
```

### 4. Migration Idempotency

Always use `CREATE TABLE IF NOT EXISTS`:

```sql
CREATE TABLE IF NOT EXISTS users (...);
```

### 5. Connection Management

Always return connections to pool:

```python
conn = get_db_connection()
try:
    # Use connection
    ...
finally:
    return_db_connection(conn)
```

## Production Considerations

### Use StatefulSet

For production, consider StatefulSet instead of Deployment:

- Ordered deployment
- Stable network identity
- Persistent storage per pod
- Better for clustered databases

### Backup Strategy

Implement regular backups:

```bash
# Example backup job
kubectl exec <postgresql-pod> -n sample-app -- \
  pg_dump -U appuser sampleapp > backup.sql
```

### Monitoring

Monitor database metrics:

- Connection pool usage
- Query performance
- Storage usage
- Replication lag (if applicable)

## Next Steps

- Add database models (ORM integration)
- Implement query logging
- Add connection retry logic
- Add database backup CronJob
