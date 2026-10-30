locals {
  project_role_assignments = flatten([
    for project_id, project in var.project_roles : [
      for role, members in project.roles : [
        for member in members : {
          project_id = project_id
          role = role
          member = member
        }
      ]
    ]
  ])
  project_role_map = {
    for item in local.project_role_assignments :
    jsonencode([item.project_id, item.role, item.member]) => item
  }
}
resource "google_project_iam_member" "project_roles" {
  for_each = local.project_role_map
  project = each.value.project_id
  role = each.value.role
  member = each.value.member
}
