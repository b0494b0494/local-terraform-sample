# Terraform Variables
# These can be set via terraform.tfvars or environment variables

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "sample-app"
}

variable "app_version" {
  description = "Application version"
  type        = string
  default     = "1.0.0"
}

variable "replica_count" {
  description = "Number of pod replicas"
  type        = number
  default     = 2
}

variable "cpu_request" {
  description = "CPU request for containers"
  type        = string
  default     = "100m"
}

variable "cpu_limit" {
  description = "CPU limit for containers"
  type        = string
  default     = "200m"
}

variable "memory_request" {
  description = "Memory request for containers"
  type        = string
  default     = "128Mi"
}

variable "memory_limit" {
  description = "Memory limit for containers"
  type        = string
  default     = "256Mi"
}

variable "log_level" {
  description = "Log level (DEBUG, INFO, WARNING, ERROR)"
  type        = string
  default     = "INFO"
}

variable "enable_ingress" {
  description = "Enable Ingress resource"
  type        = bool
  default     = false
}

variable "ingress_host" {
  description = "Ingress hostname"
  type        = string
  default     = "sample-app.local"
}

# HPA Variables
variable "enable_hpa" {
  description = "Enable Horizontal Pod Autoscaler"
  type        = bool
  default     = true
}

variable "hpa_min_replicas" {
  description = "Minimum number of replicas for HPA"
  type        = number
  default     = 2
}

variable "hpa_max_replicas" {
  description = "Maximum number of replicas for HPA"
  type        = number
  default     = 10
}

variable "hpa_target_cpu" {
  description = "Target CPU utilization percentage for HPA"
  type        = number
  default     = 70
}

# Storage Variables
variable "enable_persistent_storage" {
  description = "Enable persistent storage (PV/PVC)"
  type        = bool
  default     = false
}

variable "storage_size" {
  description = "Storage size (e.g., 1Gi, 10Gi)"
  type        = string
  default     = "1Gi"
}

variable "storage_host_path" {
  description = "Host path for local storage (Minikube/kind)"
  type        = string
  default     = "/tmp/k8s-storage"
}

# Monitoring Variables
variable "enable_prometheus" {
  description = "Enable Prometheus monitoring"
  type        = bool
  default     = false
}

variable "enable_grafana" {
  description = "Enable Grafana dashboards"
  type        = bool
  default     = false
}

variable "enable_loki" {
  description = "Enable Loki log aggregation"
  type        = bool
  default     = false
}

# Cache Variables
variable "enable_redis" {
  description = "Enable Redis cache layer"
  type        = bool
  default     = true
}

variable "redis_storage_size" {
  description = "Storage size for Redis persistent volume"
  type        = string
  default     = "1Gi"
}

# Network Policy Variables
variable "enable_network_policies" {
  description = "Enable Network Policies for pod-to-pod communication control"
  type        = bool
  default     = false  # Note: Requires CNI plugin that supports Network Policies (e.g., Calico, Cilium)
}
