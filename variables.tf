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
