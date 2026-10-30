resource "google_service_account_iam_member" "gke_workload_identity" {
  for_each = local.gke_workload_identity_map

  service_account_id = google_service_account.managed[split("@", each.key)[0]].name
  role               = "roles/iam.workloadIdentityUser"
  member             = each.value
}
