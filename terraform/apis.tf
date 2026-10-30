resource "google_project_service" "enabled_apis" {
  for_each = local.enabled_api_map

  project            = each.value.project_id
  service            = each.value.service
  disable_on_destroy = false
}
