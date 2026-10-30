resource "google_project_iam_member" "service_account_roles" {
  for_each = local.service_account_role_map

  project = each.value.project_id
  role    = each.value.role
  member  = google_service_account.managed[each.value.service_account_key].member
}
