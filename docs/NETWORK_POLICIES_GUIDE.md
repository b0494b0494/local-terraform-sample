# Network Policies Guide

This guide explains how to use Network Policies to control pod-to-pod communication in Kubernetes.

## Overview

Network Policies provide fine-grained control over network traffic between pods. They act as a firewall at the pod level, allowing you to implement zero-trust networking principles.

## Prerequisites

**Important**: Network Policies require a CNI (Container Network Interface) plugin that supports them:

- **Calico** (recommended for Minikube)
- **Cilium**
- **Weave Net**
- **Antrea**

Most local Kubernetes clusters (Minikube, kind, k3d) do **not** support Network Policies by default.

## Enabling Network Policies in Local Clusters

### Minikube with Calico

```bash
# Start Minikube with Calico CNI
minikube start --network-plugin=cni --cni=calico

# Or install Calico addon
minikube start
minikube addons enable calico
```

### kind with Calico

```bash
# Create cluster with Calico
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  disableDefaultCNI: true
nodes:
  - role: control-plane
EOF

# Install Calico
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
```

### k3d

k3d uses Flannel by default, which doesn't support Network Policies. You'll need to use a different CNI:

```bash
# Use Calico with k3d (requires custom setup)
```

## Network Policies in This Project

### 1. Default Deny-All Policy

**Purpose**: Blocks all traffic by default, enforcing explicit allow rules.

```hcl
resource "kubernetes_network_policy" "default_deny_all" {
  spec {
    pod_selector { match_labels = {} }  # Matches all pods
    policy_types = ["Ingress", "Egress"]
    # No rules = deny all
  }
}
```

### 2. Allow App to Redis

**Purpose**: Allows application pods to connect to Redis cache.

**Rules**:
- Egress from app pods (`app=sample-app`)
- To Redis pods (`app=sample-app-redis`)
- Port 6379 (TCP)

### 3. Allow Service to App

**Purpose**: Allows Kubernetes Service to route traffic to application pods.

**Rules**:
- Ingress to app pods
- From same namespace (via Service)
- From monitoring namespace (for Prometheus)
- Port 8080 (TCP)

### 4. Allow DNS

**Purpose**: Required for Service discovery (DNS queries).

**Rules**:
- Egress to kube-dns
- Port 53 (TCP and UDP)

### 5. Allow Monitoring Scrape

**Purpose**: Allows Prometheus to scrape metrics from app pods.

**Rules**:
- Ingress to app pods
- From monitoring namespace
- From Prometheus pods
- Port 8080 (TCP)

## Usage

### Enable Network Policies

```bash
# Via terraform.tfvars
enable_network_policies = true

# Or via command line
terraform apply -var="enable_network_policies=true"
```

### Verify Network Policies

```bash
# List all network policies
kubectl get networkpolicies -n sample-app

# Describe a specific policy
kubectl describe networkpolicy sample-app-default-deny -n sample-app
```

### Test Network Isolation

1. **Test allowed traffic** (should work):
```bash
# App should connect to Redis
kubectl exec -it <app-pod> -n sample-app -- redis-cli -h sample-app-redis ping
```

2. **Test blocked traffic** (should fail):
```bash
# Try to connect to a service not in allow list
kubectl exec -it <app-pod> -n sample-app -- nc -zv <other-service> 8080
# Should timeout or be blocked
```

## Common Patterns

### Pattern 1: Namespace Isolation

Allow traffic only within the same namespace:

```hcl
ingress {
  from {
    namespace_selector {
      match_labels = {
        name = kubernetes_namespace.sample_app.metadata[0].name
      }
    }
  }
}
```

### Pattern 2: Specific Pod Communication

Allow traffic between specific pods:

```hcl
egress {
  to {
    pod_selector {
      match_labels = {
        app = "redis"
      }
    }
  }
  ports {
    port     = "6379"
    protocol = "TCP"
  }
}
```

### Pattern 3: Cross-Namespace Access

Allow traffic from another namespace:

```hcl
ingress {
  from {
    namespace_selector {
      match_labels = {
        name = "monitoring"
      }
    }
  }
}
```

## Troubleshooting

### Network Policy Not Working

1. **Check CNI support**:
```bash
kubectl get pods -n kube-system | grep -i calico
# or
kubectl get pods -n kube-system | grep -i cilium
```

2. **Check Network Policy resource**:
```bash
kubectl get networkpolicies -n sample-app
kubectl describe networkpolicy <name> -n sample-app
```

3. **Test connectivity**:
```bash
# From app pod
kubectl exec -it <app-pod> -n sample-app -- ping <target-pod-ip>

# Check DNS
kubectl exec -it <app-pod> -n sample-app -- nslookup sample-app-redis
```

### Common Issues

**Issue**: DNS not working
- **Solution**: Ensure DNS egress policy allows port 53 (UDP/TCP)

**Issue**: Service not routing traffic
- **Solution**: Check ingress policy allows traffic from Service

**Issue**: Redis connection fails
- **Solution**: Verify egress policy allows traffic to Redis pod selector

## Best Practices

1. **Start with deny-all**: Default deny, then explicitly allow needed traffic
2. **Use labels**: Leverage pod labels for flexible selectors
3. **Test incrementally**: Enable one policy at a time and test
4. **Document rules**: Comment why each rule exists
5. **Monitor logs**: Check pod logs for connection failures

## Security Benefits

- **Zero-trust model**: No implicit trust between pods
- **Attack surface reduction**: Limit lateral movement
- **Compliance**: Meet security requirements
- **Defense in depth**: Multiple layers of security

## Next Steps

- Explore more advanced patterns (port ranges, IP blocks)
- Integrate with service mesh (Istio, Linkerd)
- Monitor policy violations
- Automate policy generation from service discovery
