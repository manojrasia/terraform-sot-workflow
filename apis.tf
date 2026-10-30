resource "google_project_service" "enabled_apis" {
  for_each = {
    for item in flatten([
      for project_id, services in var.project_apis : [
        for service in services : {
          project_id = project_id
          service = service
        }
      ]
    ]) : "${item.project_id}/${item.service}" => item
  }
  project = each.value.project_id
  service = each.value.service
  disable_on_destroy = false
}
