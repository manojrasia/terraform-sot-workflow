resource "google_project_iam_member" "project_roles" {
  for_each = local.project_role_map

  project = each.value.project_id
  role    = each.value.role
  member  = each.value.member
}
