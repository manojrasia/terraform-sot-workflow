resource "google_service_account" "managed" {
  for_each = var.service_accounts

  project      = each.value.project_id
  account_id   = each.value.account_id
  display_name = each.value.display_name
  description  = each.value.description
}
