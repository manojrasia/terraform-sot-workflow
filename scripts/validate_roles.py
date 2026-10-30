#!/usr/bin/env python3
"""Validate roles.json before Terraform runs."""

import json
import re
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "roles.json"
MEMBER_RE = re.compile(r"^(user|group|serviceAccount|domain):[^\\s]+$")


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main():
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read valid JSON: {exc}")

    projects = data.get("projects")
    if not isinstance(projects, dict) or not projects:
        fail("'projects' must be a non-empty object")

    seen = set()
    for project_id, project in projects.items():
        if not isinstance(project_id, str) or not project_id.strip():
            fail("Project IDs must be non-empty strings")
        roles = project.get("roles") if isinstance(project, dict) else None
        if not isinstance(roles, dict) or not roles:
            fail(f"{project_id}: roles must be a non-empty object")
        for role, members in roles.items():
            if not isinstance(role, str) or not role.startswith("roles/"):
                fail(f"{project_id}: invalid role {role!r}")
            if not isinstance(members, list) or not members:
                fail(f"{project_id}/{role}: members must be a non-empty list")
            for member in members:
                if not isinstance(member, str) or not MEMBER_RE.match(member):
                    fail(f"{project_id}/{role}: invalid member {member!r}")
                key = (project_id, role, member)
                if key in seen:
                    fail(f"Duplicate assignment: {key}")
                seen.add(key)

    print(f"Validation successful: {len(seen)} IAM assignments found.")


if __name__ == "__main__":
    main()
