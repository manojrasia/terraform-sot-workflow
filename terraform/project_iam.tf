resource "google_project_iam_member" "standard_role_bindings" {
  for_each = local.project_role_map

  project = each.value.project_id
  role    = each.value.role
  member  = each.value.member
}
