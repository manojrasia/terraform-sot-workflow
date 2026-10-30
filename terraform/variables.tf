variable "project_vars" {
  description = "Project-level metadata and defaults for the single existing GCP project."
  type = map(object({
    environment = string
    region      = string
    labels      = map(string)
  }))
}

variable "enabled_api_services" {
  description = "Google APIs to enable in the single project declared by project_vars."
  type        = list(string)
  default     = []
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
