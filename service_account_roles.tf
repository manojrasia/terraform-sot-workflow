resource "google_project_iam_member" "service_account_roles" {
  for_each = {
    for item in flatten([
      for assignment in var.service_account_roles : [
        for role in assignment.roles : {
          project_id = assignment.project_id
          service_account_email = assignment.service_account_email
          role = role
        }
      ]
    ]) : jsonencode([item.project_id, item.role, item.service_account_email]) => item
  }
  project = each.value.project_id
  role = each.value.role
  member = "serviceAccount:${each.value.service_account_email}"
}
