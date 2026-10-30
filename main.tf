locals {
  iam_config = jsondecode(file("${path.module}/roles.json"))

  assignments = flatten([
    for project_id, project in local.iam_config.projects : [
      for role, members in project.roles : [
        for member in members : {
          project_id = project_id
          role       = role
          member     = member
        }
      ]
    ]
  ])

  iam_map = {
    for assignment in local.assignments :
    jsonencode([assignment.project_id, assignment.role, assignment.member]) => assignment
  }
}

resource "google_project_iam_member" "managed" {
  for_each = local.iam_map
  project  = each.value.project_id
  role     = each.value.role
  member   = each.value.member
}
