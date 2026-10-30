output "enabled_apis" {
  value = { for key, api in google_project_service.enabled_apis : key => api.service }
}
output "project_iam_members" {
  value = { for key, binding in google_project_iam_member.project_roles : key => {
    project = binding.project
    role = binding.role
    member = binding.member
  } }
}
