# Blue-Green Deployment Module Variables

variable "app_name" {
  description = "Application name"
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
}

variable "image" {
  description = "Container image"
  type        = string
}

variable "replicas" {
  description = "Number of replicas"
  type        = number
  default     = 2
}

variable "environment" {
  description = "Environment name (blue or green)"
  type        = string
  validation {
    condition     = contains(["blue", "green"], var.environment)
    error_message = "Environment must be 'blue' or 'green'"
  }
}

variable "version" {
  description = "Application version"
  type        = string
  default     = "1.0.0"
}

variable "cpu_request" {
  description = "CPU request"
  type        = string
  default     = "100m"
}

variable "memory_request" {
  description = "Memory request"
  type        = string
  default     = "128Mi"
}

variable "cpu_limit" {
  description = "CPU limit"
  type        = string
  default     = "500m"
}

variable "memory_limit" {
  description = "Memory limit"
  type        = string
  default     = "512Mi"
}

variable "config_map_name" {
  description = "ConfigMap name for environment variables"
  type        = string
}

variable "service_account_name" {
  description = "ServiceAccount name"
  type        = string
  default     = ""
}

variable "labels" {
  description = "Additional labels"
  type        = map(string)
  default     = {}
}
