output "project_configuration" {
  description = "Project metadata supplied by the SOT configuration."
  value       = var.project_vars
}

output "enabled_apis" {
  description = "APIs managed by this configuration."
  value       = { for key, api in google_project_service.enabled_apis : key => api.service }
}

output "managed_service_accounts" {
  description = "Google service accounts created by this configuration."
  value = {
    for key, account in google_service_account.managed : key => {
      email      = account.email
      name       = account.name
      project    = account.project
      unique_id  = account.unique_id
    }
  }
}

output "project_iam_members" {
  description = "Project IAM member bindings managed from project_roles."
  value = {
    for key, binding in google_project_iam_member.project_roles : key => {
      project = binding.project
      role    = binding.role
      member  = binding.member
    }
  }
}

output "firewall_rule_names" {
  description = "Created firewall rule names."
  value       = { for key, rule in google_compute_firewall.rules : key => rule.name }
}
