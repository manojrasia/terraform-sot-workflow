resource "google_project_service" "enabled_apis" {
  for_each = local.enabled_api_map

  project            = local.target_project_id
  service            = each.value
  disable_on_destroy = false
}
