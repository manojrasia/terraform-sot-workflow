resource "google_service_account_iam_member" "gke_workload_identity" {
  for_each = local.gke_workload_identity_map

  service_account_id = google_service_account.managed[each.value.service_account_key].name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${each.value.project_id}.svc.id.goog[${each.value.namespace}/${each.value.kubernetes_service_account}]"
}
