#!/usr/bin/env python3
"""Validate JSON source-of-truth files under sot/."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "firwall.json",
    "gke_workload_identities.auto.tfvars.json",
    "projec_apis.auto.tfvars.json",
    "project_roles.auto.tfvars.json",
    "service_account_roles.auto.tfvars.json",
    "shared_vpc_users.auto.tfvars.json",
]


def main():
    for filename in FILES:
        path = ROOT / "sot" / filename
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: {path.relative_to(ROOT)}: {exc}", file=sys.stderr)
            raise SystemExit(1)
        if not isinstance(data, dict) or not data:
            print(f"ERROR: {filename} must contain a non-empty JSON object", file=sys.stderr)
            raise SystemExit(1)
    print(f"Validated {len(FILES)} SOT JSON files.")


if __name__ == "__main__":
    main()
