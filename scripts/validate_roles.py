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

        if filename == "shared_vpc_users.auto.tfvars.json":
            try:
                validate_shared_vpc_users(data, path)
            except ValueError as exc:
                print(f"ERROR: {path.relative_to(ROOT)}: {exc}", file=sys.stderr)
                raise SystemExit(1)

    print(f"Validated {len(REQUIRED_KEYS)} SOT JSON files.")


if __name__ == "__main__":
    main()
