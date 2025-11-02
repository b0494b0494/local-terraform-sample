# RBAC (Role-Based Access Control) Guide

This guide explains ServiceAccounts and RBAC for Kubernetes security.

## What is RBAC?

RBAC provides fine-grained access control to Kubernetes resources. It defines:
- **Who** can do **what** to **which** resources
- **ServiceAccounts**: Identity for pods
- **Roles**: Permissions within a namespace
- **ClusterRoles**: Permissions cluster-wide
- **Bindings**: Connect identities to permissions

## Components in This Project

### 1. ServiceAccount
- Identity for pods
- Allows pods to authenticate and access resources
- Named: `<app-name>-sa`

### 2. Role (Namespace-scoped)
- Defines permissions within a namespace
- Allows reading ConfigMaps, Secrets, Pods
- Named: `<app-name>-role`

### 3. RoleBinding
- Connects ServiceAccount to Role
- Grants permissions to the ServiceAccount
- Named: `<app-name>-role-binding`

## How It Works

1. **ServiceAccount** is created
2. **Role** defines what permissions are needed
3. **RoleBinding** connects ServiceAccount to Role
4. **Pod** uses ServiceAccount via `service_account_name`

## Viewing RBAC Resources

```bash
# List ServiceAccounts
kubectl get serviceaccount -n <app-name>

# List Roles
kubectl get role -n <app-name>

# List RoleBindings
kubectl get rolebinding -n <app-name>

# Detailed view
kubectl describe serviceaccount <app-name>-sa -n <app-name>
kubectl describe role <app-name>-role -n <app-name>
kubectl describe rolebinding <app-name>-role-binding -n <app-name>
```

## Testing Permissions

### Test from inside a pod

```bash
# Exec into pod
kubectl exec -it -n <app-name> <pod-name> -- sh

# Try to read ConfigMap (should work)
kubectl get configmap app-config -n <app-name>

# Try to read Secrets (should work)
kubectl get secret app-secret -n <app-name>

# Try to delete a pod (should fail - no delete permission)
kubectl delete pod <other-pod> -n <app-name>
# Error: Forbidden

exit
```

### Verify Pod is Using ServiceAccount

```bash
# Check pod spec
kubectl get pod <pod-name> -n <app-name> -o jsonpath='{.spec.serviceAccountName}'
# Should output: <app-name>-sa

# Check pod security context
kubectl describe pod <pod-name> -n <app-name> | grep -A 5 "Service Account"
```

## Permission Details

Current Role permissions:

```yaml
# Can read ConfigMaps and Secrets
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]

# Can list and view pods
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]

# Can read pod logs
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
```

**Cannot do**:
- Create/update/delete resources
- Access other namespaces
- Perform cluster-wide operations

## Customizing Permissions

### Add More Permissions

Edit `rbac.tf`:

```hcl
rule {
  api_groups = [""]
  resources  = ["configmaps"]
  verbs      = ["get", "list", "create", "update"]  # Added create/update
}
```

### Reduce Permissions (Security Best Practice)

```hcl
# Most restrictive: only get (no list)
rule {
  api_groups = [""]
  resources  = ["configmaps"]
  verbs      = ["get"]  # Removed "list"
}
```

## Common RBAC Patterns

### Pattern 1: Read-Only Access
```hcl
verbs = ["get", "list"]  # Can view but not modify
```

### Pattern 2: Full Access
```hcl
verbs = ["get", "list", "create", "update", "patch", "delete"]
```

### Pattern 3: Write-Only (Rare)
```hcl
verbs = ["create", "update"]  # Can write but not read
```

## ClusterRole vs Role

### Role (Namespace-scoped)
- ? Used in `rbac.tf`
- ? Permissions only within namespace
- ? Better security (principle of least privilege)

### ClusterRole (Cluster-scoped)
- ?? Permissions across entire cluster
- ?? Used for cluster-wide resources (nodes, CRDs)
- ?? Use carefully (security risk)

Example use cases for ClusterRole:
- Reading nodes across cluster
- Managing cluster-level custom resources
- Cluster administration tasks

## Security Best Practices

### 1. Principle of Least Privilege
- Grant only minimum necessary permissions
- Start restrictive, add permissions as needed

### 2. Use ServiceAccounts
- ? Every pod should have a ServiceAccount
- ? Don't use `default` ServiceAccount for apps

### 3. Separate ServiceAccounts
- Different apps = different ServiceAccounts
- Easier to audit and manage permissions

### 4. Regular Audits
```bash
# Review all ServiceAccounts
kubectl get serviceaccount --all-namespaces

# Review all Roles
kubectl get role --all-namespaces

# Check what a ServiceAccount can do
kubectl auth can-i --list --as=system:serviceaccount:<namespace>:<sa-name> -n <namespace>
```

## Testing RBAC

### Test Permissions

```bash
# Can the ServiceAccount read ConfigMaps?
kubectl auth can-i get configmaps \
  --as=system:serviceaccount:<namespace>:<app-name>-sa \
  -n <namespace>

# Can it delete pods? (should be false)
kubectl auth can-i delete pods \
  --as=system:serviceaccount:<namespace>:<app-name>-sa \
  -n <namespace>
```

### Simulate Access

```bash
# Test API access
kubectl run test-pod --serviceaccount=<app-name>-sa \
  -n <namespace> --image=busybox --restart=Never \
  --rm -it -- sh

# Inside pod, try kubectl commands
kubectl get configmap  # Should work
kubectl delete pod xyz # Should fail
```

## Common Issues

### Pod Can't Access Resources

**Symptoms**: Permission denied errors

**Causes**:
1. ServiceAccount not assigned to pod
2. RoleBinding missing or incorrect
3. Permissions insufficient

**Solutions**:
```bash
# Check ServiceAccount assignment
kubectl get pod <pod> -o jsonpath='{.spec.serviceAccountName}'

# Check RoleBinding
kubectl get rolebinding <app-name>-role-binding -n <namespace>

# Verify permissions
kubectl describe role <app-name>-role -n <namespace>
```

### ServiceAccount Token Missing

**Cause**: Kubernetes version or API server configuration

**Solution**: Usually automatic in modern Kubernetes versions

## Integration with Cloud Providers

### AWS EKS IAM Roles

```hcl
annotations = {
  "eks.amazonaws.com/role-arn" = "arn:aws:iam::ACCOUNT:role/app-role"
}
```

### Google GKE Workload Identity

```hcl
annotations = {
  "iam.gke.io/gcp-service-account" = "app@PROJECT.iam.gserviceaccount.com"
}
```

### Azure AKS Pod Identity

```hcl
annotations = {
  "aadpodidbinding" = "app-identity"
}
```

## Next Steps

- Network Policies (network-level security)
- Pod Security Standards
- OPA Gatekeeper policies
- Audit logging
