resource "google_project_iam_member" "host_project_network_access" {
  for_each = {
    for binding in var.shared_vpc_users :
    jsonencode([binding.host_project_id, binding.role, binding.member]) => binding
  }
  project = each.value.host_project_id
  role = each.value.role
  member = each.value.member
}
