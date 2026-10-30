# GCP SOT Terraform GitOps

This repository uses JSON files under `sot/` as the source of truth and Terraform code under `terraform/` to manage selected GCP foundation and IAM configuration. The current dummy configuration is intentionally scoped to one GCP project: `dummy-dev-project`.

## Repository layout

```text
.
├── sot/
│   ├── firwall.json
│   ├── gke_workload_identities.auto.tfvars.json
│   ├── projec_apis.auto.tfvars.json
│   ├── project_roles.auto.tfvars.json
│   ├── project_vars.auto.tfvars.json
│   ├── service_account.auto.tfvars.json
│   ├── service_account_roles.auto.tfvars.json
│   └── shared_vpc_users.auto.tfvars.json
├── terraform/
│   ├── versions.tf
│   ├── variables.tf
│   ├── main.tf
│   ├── apis.tf
│   ├── project_iam.tf
│   ├── service_accounts.tf
│   ├── service_account_roles.tf
│   ├── shared_vpc.tf
│   ├── gke_workload_identity.tf
│   ├── firewall.tf
│   └── outputs.tf
├── .github/workflows/terraform-iam.yml
└── scripts/validate_sot_json.py
```

## SOT file responsibilities

| File | Terraform input | Purpose |
|---|---|---|
| `firwall.json` | `firewall_rules` | VPC firewall rules |
| `gke_workload_identities.auto.tfvars.json` | `gke_workload_identities` | Google service account email to GKE Kubernetes service-account principal mappings |
| `projec_apis.auto.tfvars.json` | `project_apis` | APIs enabled in `dummy-dev-project` |
| `project_roles.auto.tfvars.json` | `project_roles` | Project IAM role/member assignments |
| `project_vars.auto.tfvars.json` | `project_vars` | Project environment, region, and labels metadata |
| `service_account.auto.tfvars.json` | `service_accounts` | Google service accounts to create |
| `service_account_roles.auto.tfvars.json` | `service_account_roles` | Project roles granted to managed service accounts |
| `shared_vpc_users.auto.tfvars.json` | `shared_vpc_users` | Subnet-level Shared VPC IAM members, keyed by full subnet resource path |

The requested spellings `firwall.json` and `projec_apis.auto.tfvars.json` are retained. Every SOT example is currently consolidated into `dummy-dev-project`.

## Terraform resources

- `google_project_service` enables APIs.
- `google_project_iam_member` manages individual project IAM members and service-account project roles.
- `google_service_account` creates the Google service accounts declared in the SOT.
- `google_service_account_iam_member` grants `roles/iam.workloadIdentityUser` to the GKE Kubernetes service-account principal.
- `google_compute_subnetwork_iam_member` grants `roles/compute.networkUser` to each declared member on the specified Shared VPC subnet.\n- `google_compute_firewall` creates the declared VPC firewall rules.

The project variables file is metadata for existing projects; this configuration does not create GCP projects. The referenced projects, VPC networks, and GKE clusters must already exist. Service accounts listed in `service_account.auto.tfvars.json` are created by Terraform.


## Shared VPC subnet access

The `shared_vpc_users.auto.tfvars.json` file maps each full subnet resource path to a list of IAM members. The dummy example uses `dummy-dev-project` as the network project. Terraform creates one subnet-level IAM member binding for every member in each list.

Example:

```json
{
  "shared_vpc_users": {
    "projects/dummy-dev-project/regions/us-central1/subnetworks/dummy-dev-subnet": [
      "serviceAccount:payments-gsa@dummy-dev-project.iam.gserviceaccount.com",
      "group:gcp.dummy-dev-project.devops@company.com"
    ]
  }
}
```

The supported member examples are Google service accounts (`serviceAccount:`) and Google Groups (`group:gcp.<project>.<groupname>@example.com`). The subnet path supplies the host project, region, and subnet name. The Terraform implementation fixes the role to `roles/compute.networkUser`.

Use the full resource path format `projects/PROJECT_ID/regions/REGION/subnetworks/SUBNET_NAME`. The referenced host project and subnet must already exist. Adding a member creates a binding; removing a member removes that member's binding. Review plans carefully before applying IAM removals.

## Workload Identity

The workload identity file maps each Google service account email (JSON key) to the GKE Kubernetes service-account principal (JSON value). The Google service accounts must exist or be created by this Terraform configuration. Create the Kubernetes service accounts in their namespaces and annotate each KSA with its corresponding GSA email. For example:

```yaml
iam.gke.io/gcp-service-account: payments-gsa@dummy-dev-project.iam.gserviceaccount.com
```

The Terraform binding grants `roles/iam.workloadIdentityUser` on the GSA to the KSA principal. The JSON format is:

```text
"gsa-email@PROJECT_ID.iam.gserviceaccount.com": "serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/KSA_NAME]"
```

## Firewall safety

The firewall file contains illustrative ingress and egress rules, all scoped to `dummy-dev-project` and `dummy-dev-vpc`. Review source/destination CIDRs, protocols, ports, network names, and target service accounts. The `203.0.113.0/24` and `192.0.2.0/24` ranges are documentation-only examples; replace them with approved ranges before deployment.

## Prerequisites and one-time setup

1. Install Terraform (the workflow pins Terraform `1.9.8`) and the Google Cloud CLI if running locally.
2. Replace `dummy-dev-project`, example email addresses, service-account settings, subnet and VPC network references in `sot/*.json` with your actual single target project configuration.
3. Ensure the referenced GCP projects, VPC networks, and GKE clusters already exist. The project metadata file does not create projects.
4. Create a dedicated GCS bucket for Terraform state before the first backend initialization. Enable object versioning, uniform bucket-level access, and public access prevention.
5. Replace `REPLACE_WITH_TERRAFORM_STATE_BUCKET` in `terraform/versions.tf` with the actual bucket name. Do not commit credentials or state files.
6. Configure GitHub OIDC Workload Identity Federation (WIF), restricting the provider trust to this repository and the intended branch/environment claims.
7. Create separate least-privilege plan and apply service accounts. Grant the plan identity read permissions needed to inspect the managed resources and access the state bucket. Grant the apply identity only the permissions required for the declared resources and state access.
8. Add these GitHub Actions repository secrets:
   - `WIF_PROVIDER`: full Workload Identity Provider resource name.
   - `PLAN_SERVICE_ACCOUNT`: plan service-account email.
   - `APPLY_SERVICE_ACCOUNT`: apply service-account email.
9. Protect `main`. Configure the `gcp-production` GitHub Environment with required reviewers if production approval is desired.

Do not use service-account JSON keys. Do not grant cloud credentials to untrusted fork pull requests.

## Terraform execution

Run these commands from the repository root. All Terraform commands use `-chdir=terraform`, so Terraform treats `terraform/` as the root module while the variable files are supplied from `../sot/`.

### 1. Validate the SOT JSON

```bash
python scripts/validate_sot_json.py
```

### 2. Format and initialize Terraform

```bash
terraform -chdir=terraform fmt -recursive
terraform -chdir=terraform init
```

The first `init` connects to the configured GCS backend. The bucket must already exist and your local identity must have access to it. For syntax validation without contacting the backend, use:

```bash
terraform -chdir=terraform init -backend=false
terraform -chdir=terraform validate
```

### 3. Create and review a plan

```bash
terraform -chdir=terraform plan -out=tfplan \
  -var-file=../sot/firwall.json \
  -var-file=../sot/gke_workload_identities.auto.tfvars.json \
  -var-file=../sot/projec_apis.auto.tfvars.json \
  -var-file=../sot/project_roles.auto.tfvars.json \
  -var-file=../sot/project_vars.auto.tfvars.json \
  -var-file=../sot/service_account.auto.tfvars.json \
  -var-file=../sot/service_account_roles.auto.tfvars.json \
  -var-file=../sot/shared_vpc_users.auto.tfvars.json

terraform -chdir=terraform show tfplan
```

Review every proposed API, IAM, service-account, and firewall change. Treat the plan file as sensitive because it can contain infrastructure details and sensitive values. Do not commit it or upload it to a public location.

### 4. Apply only after approval

```bash
terraform -chdir=terraform apply tfplan
```

To discard a saved plan without applying it:

```bash
rm -f terraform/tfplan
```

The apply command above applies the exact saved plan. If the configuration or state changes after planning, generate and review a new plan instead.

## GitHub Actions execution

Workflow: `.github/workflows/terraform-iam.yml`

| Event | Job | What it does |
|---|---|---|
| Pull request targeting `main` | `validate` | Validates JSON, checks Terraform formatting, initializes without backend, and validates the module |
| Same-repository pull request | `plan` | Authenticates with the read-only WIF identity, initializes the GCS backend, and runs Terraform plan |
| Push/merge to `main` | `validate`, then `apply` | Revalidates, authenticates with the apply WIF identity, creates a fresh plan, and applies it |

### Pull request execution

1. A developer edits one or more files under `sot/` or `terraform/` and opens a pull request to `main`.
2. The validation job checks all eight JSON inputs, runs `terraform fmt -check`, initializes Terraform with `-backend=false`, and runs `terraform validate`.
3. For a pull request originating from this repository, the plan job authenticates through GitHub OIDC/WIF using `PLAN_SERVICE_ACCOUNT`.
4. The plan job initializes the configured GCS backend, supplies all eight JSON files using explicit `-var-file` paths, and creates a plan.
5. The plan output is written to the GitHub Actions job summary and uploaded as a short-retention workflow artifact for review.

Fork pull requests intentionally do not receive cloud credentials. Review their source changes and rely on the credential-free validation job.

### Merge/apply execution

1. After the pull request is reviewed and merged, a push to `main` triggers the workflow.
2. The validation job runs again against the merged commit.
3. The apply job waits for validation and the configured `gcp-production` environment approval, if reviewers are configured.
4. The job authenticates with `APPLY_SERVICE_ACCOUNT` using WIF.
5. It initializes the backend, creates a fresh plan from the merged SOT files, and applies that plan.
6. The job logs and Terraform output are available in the GitHub Actions run.

The pipeline deliberately generates a new plan after merge rather than applying a plan created against an earlier pull-request state. Configure the GitHub Environment reviewers and branch protection to enforce your production approval process.

## Important safety notes

- All sample project IDs, email addresses, service-account names, and networks are placeholders. Replace them before running against GCP.
- Review firewall CIDRs, protocols, ports, and target tags before applying.
- Review IAM role assignments for least privilege.
- Removing an IAM assignment from the SOT input removes that binding if this Terraform state owns it.
- Avoid managing the same IAM project/role/member tuple from multiple Terraform states or overlapping authoritative IAM resources.
- Never commit Terraform state, plan files, credentials, or generated provider files.
