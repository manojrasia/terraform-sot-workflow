#!/usr/bin/env python3
"""Validate JSON source-of-truth files under sot/."""

import ipaddress
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_KEYS = {
    "firwall.json": "firewall_rules",
    "gke_workload_identities.auto.tfvars.json": "gke_workload_identities",
    "projec_apis.auto.tfvars.json": "enabled_api_services",
    "project_roles.auto.tfvars.json": "project_roles",
    "service_account_roles.auto.tfvars.json": "service_account_roles",
    "shared_vpc_users.auto.tfvars.json": "shared_vpc_users",
    "project_vars.auto.tfvars.json": "project_vars",
    "service_account.auto.tfvars.json": "service_accounts",
}


def validate_enabled_api_services(data, path):
    services = data["enabled_api_services"]
    if not isinstance(services, list) or not services:
        raise ValueError("enabled_api_services must be a non-empty array")
    if any(not isinstance(service, str) or not re.fullmatch(r"[a-z0-9-]+\.googleapis\.com", service) for service in services):
        raise ValueError("enabled_api_services entries must be valid Google API service names")
    if len(services) != len(set(services)):
        raise ValueError("enabled_api_services contains duplicate API names")


def validate_project_vars(data, path):
    projects = data["project_vars"]
    if not isinstance(projects, dict) or len(projects) != 1:
        raise ValueError("project_vars must contain exactly one project for this single-project configuration")


def validate_firewall_rules(data, path):
    rules = data["firewall_rules"]
    if not isinstance(rules, list):
        raise ValueError("firewall_rules must be an array of firewall rule objects")
    names = set()
    for index, rule in enumerate(rules):
        label = f"firewall_rules[{index}]"
        if not isinstance(rule, dict):
            raise ValueError(f"{label} must be an object")
        required = {"project_id", "name", "action", "direction", "rules", "target_network_name"}
        missing = required - rule.keys()
        if missing:
            raise ValueError(f"{label} is missing required fields: {', '.join(sorted(missing))}")
        if rule["name"] in names:
            raise ValueError(f"duplicate firewall rule name: {rule['name']!r}")
        names.add(rule["name"])
        if rule["action"] not in {"ALLOW", "DENY"}:
            raise ValueError(f"{label}.action must be ALLOW or DENY")
        if rule["direction"] not in {"INGRESS", "EGRESS"}:
            raise ValueError(f"{label}.direction must be INGRESS or EGRESS")
        if not isinstance(rule["rules"], list) or not rule["rules"]:
            raise ValueError(f"{label}.rules must be a non-empty array")
        for field in ("source_ranges", "destination_ranges"):
            for cidr in rule.get(field, []):
                try:
                    ipaddress.ip_network(cidr, strict=False)
                except ValueError as exc:
                    raise ValueError(f"{label}.{field} has invalid CIDR {cidr!r}") from exc
        for protocol_rule in rule["rules"]:
            if not isinstance(protocol_rule, dict) or "protocol" not in protocol_rule:
                raise ValueError(f"{label}.rules entries must contain protocol")
            protocol = str(protocol_rule["protocol"]).lower()
            if protocol not in {"tcp", "udp", "icmp", "esp", "ah", "ipip", "sctp"}:
                raise ValueError(f"{label} has unsupported protocol {protocol!r}")
            for port in protocol_rule.get("ports", []):
                if not str(port).isdigit() or not 1 <= int(port) <= 65535:
                    raise ValueError(f"{label} has invalid port {port!r}")
        if rule["direction"] == "INGRESS" and rule.get("destination_ranges"):
            raise ValueError(f"{label}: destination_ranges are not valid for ingress firewall rules")
        if rule["direction"] == "EGRESS" and rule.get("source_ranges"):
            raise ValueError(f"{label}: source_ranges are not valid for egress firewall rules")


def validate_shared_vpc_users(data, path):
    users = data["shared_vpc_users"]
    if not isinstance(users, dict):
        raise ValueError("shared_vpc_users must be an object mapping subnet paths to member arrays")
    subnet_pattern = re.compile(r"^projects/[^/]+/regions/[^/]+/subnetworks/[^/]+$")
    for subnet, members in users.items():
        if not subnet_pattern.fullmatch(subnet):
            raise ValueError(f"invalid subnet resource path: {subnet!r}")
        if not isinstance(members, list) or not members:
            raise ValueError(f"members for {subnet!r} must be a non-empty array")
        for member in members:
            if not isinstance(member, str):
                raise ValueError(f"member entries for {subnet!r} must be strings")
            if member.startswith("serviceAccount:") or re.fullmatch(r"group:gcp\.[^@\s]+@[^@\s]+", member):
                continue
            raise ValueError(f"unsupported Shared VPC IAM member: {member!r}")


def validate_gke_workload_identities(data, path):
    mappings = data["gke_workload_identities"]
    if not isinstance(mappings, dict):
        raise ValueError("gke_workload_identities must map GSA emails to KSA principals")
    gsa_pattern = re.compile(r"^[a-z][a-z0-9-]*@[a-z][a-z0-9-]*\.iam\.gserviceaccount\.com$")
    ksa_pattern = re.compile(r"^serviceAccount:([a-z][a-z0-9-]*)\.svc\.id\.goog\[([a-z0-9-]+)/([a-z0-9-]+)\]$")
    for gsa_email, ksa_principal in mappings.items():
        if not isinstance(gsa_email, str) or not gsa_pattern.fullmatch(gsa_email):
            raise ValueError(f"invalid Google service account email key: {gsa_email!r}")
        match = ksa_pattern.fullmatch(ksa_principal) if isinstance(ksa_principal, str) else None
        if not match:
            raise ValueError(f"invalid KSA principal for {gsa_email!r}: {ksa_principal!r}")
        gsa_project = gsa_email.split("@", 1)[1].split(".", 1)[0]
        if match.group(1) != gsa_project:
            raise ValueError(f"GSA and KSA project IDs do not match for {gsa_email!r}")


def main():
    loaded = {}
    for filename, expected_key in REQUIRED_KEYS.items():
        path = ROOT / "sot" / filename
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"ERROR: {path.relative_to(ROOT)}: {exc}", file=sys.stderr)
            raise SystemExit(1)
        if not isinstance(data, dict) or expected_key not in data:
            print(f"ERROR: {path.relative_to(ROOT)} must contain top-level key {expected_key!r}", file=sys.stderr)
            raise SystemExit(1)
        loaded[filename] = data

    validators = {
        "firwall.json": validate_firewall_rules,
        "gke_workload_identities.auto.tfvars.json": validate_gke_workload_identities,
        "projec_apis.auto.tfvars.json": validate_enabled_api_services,
        "project_vars.auto.tfvars.json": validate_project_vars,
        "shared_vpc_users.auto.tfvars.json": validate_shared_vpc_users,
    }
    try:
        for filename, validator in validators.items():
            validator(loaded[filename], ROOT / "sot" / filename)
    except (ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Validated {len(REQUIRED_KEYS)} SOT JSON files.")


if __name__ == "__main__":
    main()
