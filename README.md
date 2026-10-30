# GCP IAM GitOps with Terraform and GitHub Actions

This starter manages project-level IAM member bindings from roles.json. A pull request validates the configuration and creates a Terraform plan. A merge to main runs a fresh plan and applies it after any configured GitHub Environment approval.

## Files

- roles.json: desired project, role, and member assignments.
- main.tf: creates one google_project_iam_member per tuple.
- versions.tf: Google provider and GCS remote state backend.
- outputs.tf: lists managed assignments.
- scripts/validate_roles.py: validates JSON structure and duplicate entries.
- .github/workflows/terraform-iam.yml: PR plan and post-merge apply.
- architecture.mmd: Mermaid architecture diagram.

## 1. Configure roles.json

Replace sample project IDs and principals with real values. Example:

~~~json
{
  "projects": {
    "my-dev-project": {
      "roles": {
        "roles/viewer": ["user:developer@example.com"],
        "roles/cloudsql.viewer": [
          "serviceAccount:app-sa@my-dev-project.iam.gserviceaccount.com"
        ]
      }
    }
  }
}
~~~

The validator checks project IDs are non-empty, role names begin with roles/, supported member prefixes, and duplicate tuples. It does not confirm that projects, roles, or principals exist.

## 2. Create the GCS state bucket

Create a dedicated bucket before Terraform initialization. Enable uniform bucket-level access, public access prevention, and object versioning. Replace the backend bucket in versions.tf.

~~~bash
gcloud storage buckets create gs://YOUR_UNIQUE_STATE_BUCKET \
  --project=YOUR_STATE_PROJECT_ID \
  --location=us-central1 \
  --uniform-bucket-level-access \
  --public-access-prevention

gcloud storage buckets update gs://YOUR_UNIQUE_STATE_BUCKET --versioning
~~~

Grant the Terraform identities only the required access to the state bucket. The plan identity needs state read and locking permissions; the apply identity needs state read/write and locking permissions. Confirm the exact permissions against the Terraform GCS backend requirements and locking mode you use.

## 3. Configure Google Cloud Workload Identity Federation

Use GitHub OIDC / Workload Identity Federation (WIF), not a downloaded service-account JSON key.

Create a workload identity pool and GitHub OIDC provider. Configure attribute mappings for at least:

- google.subject = assertion.sub
- attribute.repository = assertion.repository
- attribute.ref = assertion.ref
- attribute.event_name = assertion.event_name

Restrict the provider attribute condition to this exact repository: manojrasia/terraform-sot-workflow. Add event and ref restrictions appropriate to your trust model. The PR plan job is restricted to same-repository pull requests; do not change it to pull_request_target.

Allow the GitHub principal set to impersonate the respective service accounts with roles/iam.workloadIdentityUser. Keep plan and apply service accounts separate.

### Suggested IAM separation

| Identity | Suggested permissions |
|---|---|
| Plan service account | Read project IAM policy and read/lock Terraform state; no IAM mutation permissions |
| Apply service account | Manage project IAM members only in approved target projects; read/write/lock Terraform state |

Use least privilege. Avoid broad Project Owner or Editor roles. Exact custom role permissions depend on the GCS backend locking mode and IAM operations required by your provider version.

## 4. Configure GitHub

Add these Actions repository secrets:

- WIF_PROVIDER: full provider resource name, for example projects/123456789/locations/global/workloadIdentityPools/POOL_ID/providers/PROVIDER_ID
- PLAN_SERVICE_ACCOUNT: plan service-account email
- APPLY_SERVICE_ACCOUNT: apply service-account email

Create a GitHub Environment named gcp-production. Add required reviewers if you want manual approval before apply.

Protect main: require pull requests, require the validation and plan checks, restrict direct pushes, and require review for changes to workflow files, Terraform files, and roles.json. Consider CODEOWNERS. Do not allow untrusted fork PRs to receive cloud credentials.

## 5. Run locally

Prerequisites: Terraform >= 1.5, Google Cloud CLI, and Python 3.

~~~bash
python scripts/validate_roles.py
terraform fmt -recursive
terraform init
terraform validate
terraform plan
terraform apply
~~~

For local runs, authenticate with an appropriately scoped identity (for example, Application Default Credentials). Never commit credentials or Terraform state files.

## 6. GitOps flow

1. Change roles.json.
2. Open a pull request.
3. GitHub Actions validates JSON and Terraform configuration.
4. For same-repository PRs, a read-only WIF identity runs Terraform plan and publishes the summary.
5. Review the plan and merge the PR.
6. The gcp-production environment can require approval.
7. The workflow authenticates with the apply identity, creates a fresh plan from merged main, and applies that exact plan file.

The apply job intentionally re-plans after merge. It does not apply a plan artifact produced from the PR branch.

## Important behavior and limitations

- google_project_iam_member is non-authoritative: it manages only the specific project/role/member tuple, not every member for a role.
- Removing a tuple from roles.json causes Terraform to remove the corresponding member binding if this state owns it. Do not manage the same tuple from another state or competing IAM resource.
- Test in a non-production project first and review every plan.
- This starter does not create projects, service accounts, the WIF pool/provider, or the state bucket. Provision those separately.
- Plan output can contain project IDs, role names, and principal email addresses. Restrict repository and artifact access.
- For stronger supply-chain security, pin third-party GitHub Actions to full commit SHAs and add policy-as-code checks (for example, block Owner/Editor grants and enforce approved principals).
- Review workflow and WIF conditions before enabling production access. Workflow code alone is not a substitute for GitHub branch protection and GCP trust-policy restrictions.

## Architecture diagram

See architecture.mmd. GitHub renders Mermaid diagrams in Markdown.
