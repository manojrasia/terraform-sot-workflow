#!/usr/bin/env python3
"""Validate JSON source-of-truth files under sot/."""

import ipaddress
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "firwall.json": "firewall_rules",
    "gke_workload_identities.auto.tfvars.json": "gke_workload_identities",
    "projec_apis.auto.tfvars.json": "enabled_api_services",
    "project_roles.auto.tfvars.json": "standard_role_bindings",
    "service_account_roles.auto.tfvars.json": "service_accounts_role_bindings",
    "shared_vpc_users.auto.tfvars.json": "shared_vpc_users",
    "project_vars.auto.tfvars.json": "gcp_project",
    "service_account.auto.tfvars.json": "service_accounts",
}
GROUP_RE = re.compile(r"^group:gcp\.[^@\s]+@[^@\s]+$")
SA_RE = re.compile(r"^serviceAccount:[a-z][a-z0-9-]*@[a-z][a-z0-9-]*\.iam\.gserviceaccount\.com$")
GSA_EMAIL_RE = re.compile(r"^[a-z][a-z0-9-]*@[a-z][a-z0-9-]*\.iam\.gserviceaccount\.com$")
KSA_RE = re.compile(r"^serviceAccount:([a-z][a-z0-9-]*)\.svc\.id\.goog\[([a-z0-9-]+)/([a-z0-9-]+)\]$")


def validate_enabled_api_services(data):
    services = data["enabled_api_services"]
    if not isinstance(services, list) or not services:
        raise ValueError("enabled_api_services must be a non-empty array")
    if any(not isinstance(x, str) or not re.fullmatch(r"[a-z0-9-]+\.googleapis\.com", x) for x in services):
        raise ValueError("enabled_api_services contains an invalid Google API service name")
    if len(services) != len(set(services)):
        raise ValueError("enabled_api_services contains duplicates")


def validate_standard_role_bindings(data):
    bindings = data["standard_role_bindings"]
    if not isinstance(bindings, dict) or not bindings:
        raise ValueError("standard_role_bindings must be a non-empty object")
    for role, entries in bindings.items():
        if not isinstance(role, str) or not role.startswith("roles/"):
            raise ValueError(f"invalid IAM role: {role!r}")
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"{role} must have at least one principal")
        for entry in entries:
            principal = entry.get("principal") if isinstance(entry, dict) else None
            if not isinstance(principal, str) or not (GROUP_RE.fullmatch(principal) or SA_RE.fullmatch(principal)):
                raise ValueError(f"unsupported standard IAM principal: {principal!r}")


def validate_project_vars(data):
    required = {"authoritative", "gcp_project", "gcp_project_labels", "gcp_project_name",
                "gcp_region", "gcp_zone", "hsbc_billing_account", "folder_display_name",
                "vpc_host_project"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"project_vars is missing fields: {', '.join(sorted(missing))}")
    if not isinstance(data["gcp_project"], str) or not data["gcp_project"]:
        raise ValueError("gcp_project must be a non-empty string")
    if not isinstance(data["gcp_project_labels"], dict):
        raise ValueError("gcp_project_labels must be an object")
    if not isinstance(data["authoritative"], str):
        raise ValueError("authoritative must be a string")


def validate_service_accounts(data):
    accounts = data["service_accounts"]
    if not isinstance(accounts, dict) or not accounts:
        raise ValueError("service_accounts must be a non-empty name-to-description object")
    for name, description in accounts.items():
        if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", name):
            raise ValueError(f"invalid service account ID: {name!r}")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"service account {name!r} must have a description")


def validate_service_account_role_bindings(data, accounts):
    if data.get("service_accounts_role_bindings_version") != 1:
        raise ValueError("service_accounts_role_bindings_version must be 1")
    bindings = data["service_accounts_role_bindings"]
    if not isinstance(bindings, dict):
        raise ValueError("service_accounts_role_bindings must be an object")
    for account, role_entries in bindings.items():
        if account not in accounts:
            raise ValueError(f"role bindings reference undeclared service account {account!r}")
        if not isinstance(role_entries, list):
            raise ValueError(f"role bindings for {account!r} must be an array")
        for entry in role_entries:
            if not isinstance(entry, dict) or not {"role", "members"} <= entry.keys():
                raise ValueError(f"each role binding for {account!r} needs role and members")
            if not isinstance(entry["role"], str) or not entry["role"].startswith("roles/"):
                raise ValueError(f"invalid role in service account {account!r}")
            members = entry["members"]
            if not isinstance(members, list) or not members:
                raise ValueError(f"members for {account!r}/{entry['role']} must be non-empty")
            for member in members:
                if not isinstance(member, str) or not (GROUP_RE.fullmatch(member) or SA_RE.fullmatch(member)):
                    raise ValueError(f"unsupported service account IAM member: {member!r}")


def validate_firewall_rules(data):
    rules = data["firewall_rules"]
    if not isinstance(rules, list):
        raise ValueError("firewall_rules must be an array")
    names = set()
    for index, rule in enumerate(rules):
        label = f"firewall_rules[{index}]"
        required = {"project_id", "name", "action", "direction", "rules", "target_network_name"}
        if not isinstance(rule, dict) or not required <= rule.keys():
            raise ValueError(f"{label} is missing required firewall properties")
        if rule["name"] in names:
            raise ValueError(f"duplicate firewall rule name: {rule['name']!r}")
        names.add(rule["name"])
        if rule["action"] not in {"ALLOW", "DENY"} or rule["direction"] not in {"INGRESS", "EGRESS"}:
            raise ValueError(f"{label} has invalid action or direction")
        if not isinstance(rule["rules"], list) or not rule["rules"]:
            raise ValueError(f"{label}.rules must be a non-empty array")
        for field in ("source_ranges", "destination_ranges"):
            for cidr in rule.get(field, []):
                ipaddress.ip_network(cidr, strict=False)
        for item in rule["rules"]:
            if not isinstance(item, dict) or str(item.get("protocol", "")).lower() not in {
                "tcp", "udp", "icmp", "esp", "ah", "ipip", "sctp"
            }:
                raise ValueError(f"{label} has an invalid protocol")
            for port in item.get("ports", []):
                if not str(port).isdigit() or not 1 <= int(port) <= 65535:
                    raise ValueError(f"{label} has an invalid port: {port!r}")


def validate_shared_vpc_users(data):
    users = data["shared_vpc_users"]
    if not isinstance(users, dict):
        raise ValueError("shared_vpc_users must map subnet paths to member arrays")
    pattern = re.compile(r"^projects/[^/]+/regions/[^/]+/subnetworks/[^/]+$")
    for subnet, members in users.items():
        if not pattern.fullmatch(subnet) or not isinstance(members, list) or not members:
            raise ValueError(f"invalid subnet path or empty member list: {subnet!r}")
        if any(not isinstance(m, str) or not (GROUP_RE.fullmatch(m) or SA_RE.fullmatch(m)) for m in members):
            raise ValueError(f"unsupported Shared VPC member for {subnet!r}")


def validate_gke_workload_identities(data, accounts):
    mappings = data["gke_workload_identities"]
    if not isinstance(mappings, dict):
        raise ValueError("gke_workload_identities must map GSA emails to KSA principals")
    for email, principal in mappings.items():
        if not isinstance(email, str) or not GSA_EMAIL_RE.fullmatch(email):
            raise ValueError(f"invalid GSA email: {email!r}")
        if not isinstance(principal, str):
            raise ValueError(f"invalid KSA principal for {email!r}")
        match = KSA_RE.fullmatch(principal)
        if not match or match.group(1) != email.split("@", 1)[1].split(".", 1)[0]:
            raise ValueError(f"GSA/KSA project mismatch or invalid KSA principal for {email!r}")
        if email.split("@", 1)[0] not in accounts:
            raise ValueError(f"GKE workload identity references undeclared service account {email!r}")


def main():
    loaded = {}
    for filename, key in FILES.items():
        path = ROOT / "sot" / filename
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"ERROR: {path.relative_to(ROOT)}: {exc}")
        if not isinstance(item, dict) or key not in item:
            raise SystemExit(f"ERROR: {path.relative_to(ROOT)} must contain top-level key {key!r}")
        loaded[filename] = item

    accounts = loaded["service_account.auto.tfvars.json"]["service_accounts"]
    try:
        validate_enabled_api_services(loaded["projec_apis.auto.tfvars.json"])
        validate_standard_role_bindings(loaded["project_roles.auto.tfvars.json"])
        validate_project_vars(loaded["project_vars.auto.tfvars.json"])
        validate_service_accounts(loaded["service_account.auto.tfvars.json"])
        validate_service_account_role_bindings(loaded["service_account_roles.auto.tfvars.json"], accounts)
        validate_firewall_rules(loaded["firwall.json"])
        validate_shared_vpc_users(loaded["shared_vpc_users.auto.tfvars.json"])
        validate_gke_workload_identities(loaded["gke_workload_identities.auto.tfvars.json"], accounts)
    except (ValueError, TypeError, KeyError) as exc:
        raise SystemExit(f"ERROR: {exc}")

    print(f"Validated {len(FILES)} SOT JSON files.")


if __name__ == "__main__":
    main()
