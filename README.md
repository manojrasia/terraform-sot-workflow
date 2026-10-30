# GCP SOT Terraform GitOps

The `sot/` directory is the source of truth for selected GCP APIs, IAM assignments, GKE Workload Identity bindings, Shared VPC users, and VPC firewall rules.

## SOT inputs

| File | Variable | Purpose |
|---|---|---|
| `sot/firwall.json` | `firewall_rules` | VPC firewall rules |
| `sot/gke_workload_identities.auto.tfvars.json` | `gke_workload_identities` | GKE KSA to Google service-account federation |
| `sot/projec_apis.auto.tfvars.json` | `project_apis` | APIs enabled in each project |
| `sot/project_roles.auto.tfvars.json` | `project_roles` | Project IAM role/member assignments; replaces root roles.json |
| `sot/service_account_roles.auto.tfvars.json` | `service_account_roles` | Roles granted to Google service accounts |
| `sot/shared_vpc_users.auto.tfvars.json` | `shared_vpc_users` | Shared VPC host-project IAM members |

The requested spellings `firwall.json` and `projec_apis.auto.tfvars.json` are retained.

## Dummy values

All `dummy-*` project IDs, example project numbers, networks, service accounts, and email addresses are placeholders. Replace them before running against GCP. The sample VPC and service accounts must already exist.

## Terraform behavior

- `google_project_service` enables listed APIs.
- `google_project_iam_member` manages individual project IAM members.
- `google_service_account_iam_member` grants GKE Workload Identity User to the Kubernetes service-account principal.
- `google_compute_firewall` creates the declared firewall rules.

Terraform does not automatically load tfvars files from a subdirectory. The workflow and local command therefore pass all six files using explicit `-var-file` arguments.

## GKE Workload Identity

The Google service account must exist. Create the Kubernetes service account in the indicated namespace and annotate it with the Google service account email, for example:

```yaml
iam.gke.io/gcp-service-account: payments-gsa@dummy-dev-project.iam.gserviceaccount.com
```

The Terraform IAM binding uses the principal format:

```text
serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/KSA_NAME]
```

## Firewall review

The firewall file is an illustrative ingress example. Review source CIDRs, protocols, ports, network self-links, and target tags. Do not copy sample rules into production without security review.

## GitHub Actions

Pull requests validate JSON and Terraform and run a plan for same-repository PRs using the read-only WIF service account. A push to main creates a fresh plan and applies it using the apply service account, behind the optional `gcp-production` GitHub Environment approval.

Configure repository secrets:
- `WIF_PROVIDER`
- `PLAN_SERVICE_ACCOUNT`
- `APPLY_SERVICE_ACCOUNT`

Restrict WIF trust to this repository and intended refs/events. Protect main and use least-privilege service accounts. Do not provide cloud credentials to fork PRs.

## Backend and prerequisites

Create the GCS state bucket separately, enable object versioning, uniform bucket-level access, and public access prevention, then replace the placeholder in `versions.tf`. The workflow does not create projects, VPCs, GKE clusters, service accounts, or the WIF provider.

## Local commands

```bash
python scripts/validate_roles.py
terraform fmt -recursive
terraform init
terraform validate
terraform plan \
  -var-file=sot/firwall.json \
  -var-file=sot/gke_workload_identities.auto.tfvars.json \
  -var-file=sot/projec_apis.auto.tfvars.json \
  -var-file=sot/project_roles.auto.tfvars.json \
  -var-file=sot/service_account_roles.auto.tfvars.json \
  -var-file=sot/shared_vpc_users.auto.tfvars.json
```

Review the plan carefully. Removing an IAM assignment from the SOT input removes that binding if this state owns it. Avoid managing the same IAM tuple from multiple states or overlapping authoritative IAM resources.
