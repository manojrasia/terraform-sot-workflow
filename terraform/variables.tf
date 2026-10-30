variable "project_vars" {
  description = "Flat metadata for the single existing GCP project."
  type = object({
    authoritative        = string
    gcp_project          = string
    gcp_project_labels   = map(string)
    gcp_project_name     = string
    gcp_region           = string
    gcp_zone             = string
    hsbc_billing_account = string
    folder_display_name  = string
    vpc_host_project     = string
  })
}

variable "enabled_api_services" {
  description = "Google APIs to enable in the single project declared by project_vars."
  type        = list(string)
  default     = []
}

variable "standard_role_bindings" {
  description = "Standard project IAM roles mapped to principal objects; applied to the single project in project_vars."
  type = map(list(object({
    principal = string
  })))
  default = {}
}

variable "service_accounts" {
  description = "Logical service account names mapped to their descriptions."
  type        = map(string)
}


variable "service_accounts_role_bindings_version" {
  description = "Schema version for service account IAM role bindings."
  type        = number
  default     = 1
}

variable "service_accounts_role_bindings" {
  description = "Service account keys mapped to role and member bindings."
  type = map(list(object({
    role    = string
    members = list(string)
  })))
  default = {}
}


variable "shared_vpc_users" {
  description = "Subnet-level Shared VPC IAM members keyed by full subnet resource path."
  type        = map(list(string))
  default     = {}
}

variable "gke_workload_identities" {
  description = "Mapping of Google service account emails to GKE Kubernetes service account principals."
  type        = map(string)
  default     = {}
}

variable "firewall_rules" {
  description = "Firewall rule definitions supplied as a list in the SOT JSON."
  type = list(object({
    project_id            = string
    name                  = string
    action                = string
    description           = optional(string, "")
    direction             = string
    source_ranges         = optional(list(string), [])
    destination_ranges    = optional(list(string), [])
    rules = list(object({
      protocol = string
      ports    = optional(list(string))
    }))
    target_id              = optional(string)
    remote_id              = optional(string)
    ticket_ref             = optional(string)
    target_network_name    = string
    target_service_account = optional(string)
  }))
  default = []
}
