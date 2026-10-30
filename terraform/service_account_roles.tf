resource "google_service_account_iam_member" "service_account_role_bindings" {
  for_each = local.service_account_role_map

  service_account_id = google_service_account.managed[each.value.service_account_key].name
  role               = each.value.role
  member             = each.value.member
}
