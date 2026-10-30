resource "google_service_account" "managed" {
  for_each = var.service_accounts

  project      = var.project_vars.gcp_project
  account_id   = each.key
  display_name = each.key
  description  = each.value
}
