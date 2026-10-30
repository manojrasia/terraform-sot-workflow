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
    for assignment in var.service_account_roles : [
      for role in assignment.roles : {
        project_id          = assignment.project_id
        service_account_key = assignment.service_account_key
        role                = role
      }
    ]
  ])

  service_account_role_map = {
    for item in local.service_account_role_assignments :
    jsonencode([item.project_id, item.role, item.service_account_key]) => item
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
