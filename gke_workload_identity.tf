resource "google_service_account_iam_member" "gke_workload_identity" {
  for_each = {
    for item in var.gke_workload_identities :
    jsonencode([item.project_id, item.namespace, item.kubernetes_service_account, item.google_service_account]) => item
  }
  service_account_id = "projects/${each.value.project_id}/serviceAccounts/${each.value.google_service_account}"
  role = "roles/iam.workloadIdentityUser"
  member = "serviceAccount:${each.value.project_id}.svc.id.goog[${each.value.namespace}/${each.value.kubernetes_service_account}]"
}
