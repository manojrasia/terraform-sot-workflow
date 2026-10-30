locals {
  standard_role_binding_assignments = flatten([
    for role, bindings in var.standard_role_bindings : [
      for binding in bindings : {
        project_id = local.target_project_id
        role       = role
        member     = binding.principal
      }
    ]
  ])

  project_role_map = {
    for item in local.standard_role_binding_assignments :
    jsonencode([item.project_id, item.role, item.member]) => item
  }

  service_account_role_assignments = flatten([
    for account_key, role_bindings in var.service_accounts_role_bindings : [
      for binding in role_bindings : [
        for principal in binding.members : {
          service_account_key = account_key
          role                = binding.role
          member              = principal
        }
      ]
    ]
  ])

  service_account_role_map = {
    for assignment in local.service_account_role_assignments :
    jsonencode([assignment.service_account_key, assignment.role, assignment.member]) => assignment
  }

  shared_vpc_user_assignments = flatten([
    for subnet, members in var.shared_vpc_users : [
      for member in members : {
        subnet = subnet
        member = member
      }
    ]
  ])

  shared_vpc_user_map = {
    for item in local.shared_vpc_user_assignments :
    jsonencode([item.subnet, item.member]) => item
  }

  gke_workload_identity_map = var.gke_workload_identities

  firewall_rule_map = {
    for rule in var.firewall_rules : rule.name => rule
  }

  enabled_api_map = {
    for service in var.enabled_api_services : service => service
  }

  target_project_id = var.project_vars.gcp_project
}
