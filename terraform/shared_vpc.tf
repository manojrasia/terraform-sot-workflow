resource "google_compute_subnetwork_iam_member" "shared_vpc_users" {
  for_each = local.shared_vpc_user_map

  project    = split("/", each.value.subnet)[1]
  region     = split("/", each.value.subnet)[3]
  subnetwork = split("/", each.value.subnet)[5]

  role   = "roles/compute.networkUser"
  member = each.value.member
}
