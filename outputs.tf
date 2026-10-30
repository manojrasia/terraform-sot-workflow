output "managed_iam_members" {
  description = "IAM project, role and member tuples managed by this Terraform state."
  value = {
    for key, assignment in google_project_iam_member.managed : key => {
      project = assignment.project
      role    = assignment.role
      member  = assignment.member
    }
  }
}
