variable "project_vars" {
  description = "Project-level metadata and defaults for each existing GCP project."
  type = map(object({
    environment = string
    region      = string
    labels      = map(string)
  }))
}

variable "project_apis" {
  description = "APIs to enable, grouped by project ID."
  type        = map(list(string))
}

variable "project_roles" {
  description = "Project IAM role-to-member assignments."
  type = map(object({
    roles = map(list(string))
  }))
}

variable "service_accounts" {
  description = "Google service accounts to create, keyed by a stable logical name."
  type = map(object({
    project_id   = string
    account_id   = string
    display_name = string
    description  = string
  }))
}

variable "service_account_roles" {
  description = "Project roles to grant to service accounts declared in service_account.auto.tfvars.json."
  type = list(object({
    project_id          = string
    service_account_key = string
    roles               = list(string)
  }))
}

variable "shared_vpc_users" {
  description = "Subnet-level Shared VPC IAM members keyed by full subnet resource path."
  type        = map(list(string))
  default     = {}
}

variable "gke_workload_identities" {
  description = "GKE Kubernetes service accounts authorized to impersonate managed Google service accounts."
  type = list(object({
    project_id                 = string
    namespace                  = string
    kubernetes_service_account = string
    service_account_key        = string
  }))
}

variable "firewall_rules" {
  description = "VPC firewall ingress/egress rules keyed by a stable identifier."
  type = map(object({
    project_id    = string
    name          = string
    network       = string
    direction     = string
    priority      = number
    source_ranges = optional(list(string), [])
    target_tags   = optional(list(string), [])
    allowed = optional(list(object({
      protocol = string
      ports    = optional(list(string))
    })), [])
    denied = optional(list(object({
      protocol = string
      ports    = optional(list(string))
    })), [])
  }))
}
