resource "google_service_account_iam_member" "gke_workload_identity" {
  for_each = local.gke_workload_identity_map

  service_account_id = "projects/${split(".", split("@", each.key)[1])[0]}/serviceAccounts/${each.key}"
  role               = "roles/iam.workloadIdentityUser"
  member             = each.value
}
