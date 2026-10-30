#!/usr/bin/env python3
"""Validate JSON source-of-truth files under sot/."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_KEYS = {
    "firwall.json": "firewall_rules",
    "gke_workload_identities.auto.tfvars.json": "gke_workload_identities",
    "projec_apis.auto.tfvars.json": "project_apis",
    "project_roles.auto.tfvars.json": "project_roles",
    "service_account_roles.auto.tfvars.json": "service_account_roles",
    "shared_vpc_users.auto.tfvars.json": "shared_vpc_users",
    "project_vars.auto.tfvars.json": "project_vars",
    "service_account.auto.tfvars.json": "service_accounts",
}


def validate_shared_vpc_users(data, path):
    users = data["shared_vpc_users"]
    if not isinstance(users, dict):
        raise ValueError("shared_vpc_users must be an object mapping subnet paths to member arrays")

    subnet_pattern = re.compile(
        r"^projects/[^/]+/regions/[^/]+/subnetworks/[^/]+$"
    )
    for subnet, members in users.items():
        if not subnet_pattern.match(subnet):
            raise ValueError(
                f"invalid subnet path {subnet!r}; expected "
                "projects/PROJECT_ID/regions/REGION/subnetworks/SUBNET_NAME"
            )
        if not isinstance(members, list) or not members:
            raise ValueError(f"members for {subnet!r} must be a non-empty array")

        for member in members:
            if not isinstance(member, str):
                raise ValueError(f"member entries for {subnet!r} must be strings")
            if member.startswith("serviceAccount:"):
                continue
            if re.fullmatch(r"group:gcp\.[^@\s]+@[^@\s]+", member):
                continue
            raise ValueError(
                f"unsupported member {member!r}; expected serviceAccount:... "
                "or group:gcp.<project>.<groupname>@example.com"
            )


def validate_gke_workload_identities(data, path):
    mappings = data["gke_workload_identities"]
    if not isinstance(mappings, dict):
        raise ValueError("gke_workload_identities must be an object mapping GSA emails to KSA principals")

    gsa_pattern = re.compile(
        r"^[a-z][a-z0-9-]*@[a-z][a-z0-9-]*\.iam\.gserviceaccount\.com$"
    )
    ksa_pattern = re.compile(
        r"^serviceAccount:([a-z][a-z0-9-]*)\.svc\.id\.goog\[([a-z0-9-]+)/([a-z0-9-]+)\]$"
    )

    for gsa_email, ksa_principal in mappings.items():
        if not isinstance(gsa_email, str) or not gsa_pattern.fullmatch(gsa_email):
            raise ValueError(f"invalid Google service account email key: {gsa_email!r}")
        if not isinstance(ksa_principal, str):
            raise ValueError(f"KSA principal for {gsa_email!r} must be a string")

        match = ksa_pattern.fullmatch(ksa_principal)
        if not match:
            raise ValueError(
                f"invalid KSA principal {ksa_principal!r}; expected "
                "serviceAccount:PROJECT_ID.svc.id.goog[NAMESPACE/KSA_NAME]"
            )

        gsa_project = gsa_email.split("@", 1)[1].split(".", 1)[0]
        if match.group(1) != gsa_project:
            raise ValueError(
                f"project mismatch: GSA {gsa_email!r} and KSA principal "
                f"{ksa_principal!r} must use the same project ID"
            )


def main():
    for filename, expected_key in REQUIRED_KEYS.items():
        path = ROOT / "sot" / filename
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: {path.relative_to(ROOT)}: {exc}", file=sys.stderr)
            raise SystemExit(1)

        if not isinstance(data, dict) or expected_key not in data:
            print(
                f"ERROR: {path.relative_to(ROOT)} must contain top-level key {expected_key!r}",
                file=sys.stderr,
            )
            raise SystemExit(1)

        try:
            if filename == "shared_vpc_users.auto.tfvars.json":
                validate_shared_vpc_users(data, path)
            elif filename == "gke_workload_identities.auto.tfvars.json":
                validate_gke_workload_identities(data, path)
        except ValueError as exc:
            print(f"ERROR: {path.relative_to(ROOT)}: {exc}", file=sys.stderr)
            raise SystemExit(1)

    print(f"Validated {len(REQUIRED_KEYS)} SOT JSON files.")


if __name__ == "__main__":
    main()
