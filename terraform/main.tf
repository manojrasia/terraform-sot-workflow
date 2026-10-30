locals {
  project_role_assignments = flatten([
    for project_id, project in var.project_roles : [
      for role, members in project.roles : [
        for member in members : {
          project_id = project_id
          role       = role
          member     = member
        }
      ]
    ]
  ])

  project_role_map = {
    for item in local.project_role_assignments :
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

  shared_vpc_user_map = {
    for item in var.shared_vpc_users :
    jsonencode([item.host_project_id, item.role, item.member]) => item
  }

  gke_workload_identity_map = {
    for item in var.gke_workload_identities :
    jsonencode([item.project_id, item.namespace, item.kubernetes_service_account, item.service_account_key]) => item
  }

  enabled_api_map = {
    for item in flatten([
      for project_id, services in var.project_apis : [
        for service in services : {
          project_id = project_id
          service    = service
        }
      ]
    ]) : "${item.project_id}/${item.service}" => item
  }
}
