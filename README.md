# GCP SOT Terraform GitOps

This repository uses JSON files under `sot/` as the source of truth and Terraform code under `terraform/` to manage selected GCP foundation and IAM configuration.

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
└── scripts/validate_roles.py
```

## SOT file responsibilities

| File | Terraform input | Purpose |
|---|---|---|
| `firwall.json` | `firewall_rules` | VPC firewall rules |
| `gke_workload_identities.auto.tfvars.json` | `gke_workload_identities` | GKE Kubernetes SA to Google SA Workload Identity bindings |
| `projec_apis.auto.tfvars.json` | `project_apis` | APIs enabled per project |
| `project_roles.auto.tfvars.json` | `project_roles` | Project IAM role/member assignments |
| `project_vars.auto.tfvars.json` | `project_vars` | Project environment, region, and labels metadata |
| `service_account.auto.tfvars.json` | `service_accounts` | Google service accounts to create |
| `service_account_roles.auto.tfvars.json` | `service_account_roles` | Project roles granted to managed service accounts |
| `shared_vpc_users.auto.tfvars.json` | `shared_vpc_users` | Shared VPC host-project IAM grants |

The requested spellings `firwall.json` and `projec_apis.auto.tfvars.json` are retained.

## Terraform resources

- `google_project_service` enables APIs.
- `google_project_iam_member` manages individual project IAM members and service-account project roles.
- `google_service_account` creates the Google service accounts declared in the SOT.
- `google_service_account_iam_member` grants `roles/iam.workloadIdentityUser` to the GKE Kubernetes service-account principal.
- `google_compute_firewall` creates the declared VPC firewall rules.

The project variables file is metadata for existing projects; this configuration does not create GCP projects. The referenced projects, VPC networks, and GKE clusters must already exist. Service accounts listed in `service_account.auto.tfvars.json` are created by Terraform.

## Workload Identity

The workload identity entries refer to service-account keys declared in `service_account.auto.tfvars.json`. Create the Kubernetes service accounts in their namespaces and annotate them with the corresponding Google service account email. For example:

```yaml
iam.gke.io/gcp-service-account: payments-gsa@dummy-dev-project.iam.gserviceaccount.com
```

The Terraform binding uses the GKE workload identity principal format:

```text
serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/KSA_NAME]
```

## Firewall safety

The firewall file is an illustrative ingress example. Review source CIDRs, protocols, ports, network self-links, and target tags. Avoid broad ingress ranges and administrative ports in production.

## GitHub Actions

The workflow:
1. Validates all eight SOT JSON files.
2. Runs Terraform formatting and validation from the `terraform/` directory.
3. Runs a PR plan using a read-only WIF identity for same-repository PRs.
4. After merge, creates a fresh plan and applies it using a separate apply WIF identity.
5. Uses the `gcp-production` GitHub Environment for optional required reviewers.

Configure repository secrets:
- `WIF_PROVIDER`
- `PLAN_SERVICE_ACCOUNT`
- `APPLY_SERVICE_ACCOUNT`

Restrict WIF trust to this repository and intended refs/events. Protect `main`, use least-privilege identities, and do not grant cloud credentials to untrusted fork PRs.

## Backend and prerequisites

Create the GCS state bucket separately, enable object versioning, uniform bucket-level access, and public access prevention, then replace the bucket placeholder in `terraform/versions.tf`. The workflow does not create projects, VPCs, GKE clusters, or the WIF provider.

## Run locally

Run the JSON validation from the repository root:

```bash
python scripts/validate_roles.py
```

Run Terraform from the `terraform/` module directory. The explicit `-var-file` arguments are needed because the JSON files live outside the module directory:

```bash
terraform -chdir=terraform fmt -recursive
terraform -chdir=terraform init
terraform -chdir=terraform validate
terraform -chdir=terraform plan \
  -var-file=../sot/firwall.json \
  -var-file=../sot/gke_workload_identities.auto.tfvars.json \
  -var-file=../sot/projec_apis.auto.tfvars.json \
  -var-file=../sot/project_roles.auto.tfvars.json \
  -var-file=../sot/service_account_roles.auto.tfvars.json \
  -var-file=../sot/shared_vpc_users.auto.tfvars.json \
  -var-file=../sot/project_vars.auto.tfvars.json \
  -var-file=../sot/service_account.auto.tfvars.json
```

All `dummy-*` project IDs, example email addresses, networks, and service-account values are placeholders. Replace them before running against GCP. Review the plan carefully; removing an IAM assignment from the SOT input removes that binding if this state owns it. Avoid managing the same IAM tuple from multiple Terraform states.
