resource "google_project_iam_member" "shared_vpc_users" {
  for_each = local.shared_vpc_user_map

  project = each.value.host_project_id
  role    = each.value.role
  member  = each.value.member
}
