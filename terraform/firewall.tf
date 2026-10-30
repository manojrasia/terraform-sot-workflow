resource "google_compute_firewall" "rules" {
  for_each = local.firewall_rule_map

  project     = each.value.project_id
  name        = each.value.name
  description = each.value.description
  network     = "projects/${each.value.project_id}/global/networks/${each.value.target_network_name}"
  direction   = each.value.direction
  priority    = 1000

  source_ranges      = each.value.source_ranges
  destination_ranges = each.value.destination_ranges

  target_service_accounts = each.value.target_service_account == null ? [] : [
    each.value.target_service_account
  ]

  dynamic "allow" {
    for_each = each.value.action == "ALLOW" ? each.value.rules : []
    content {
      protocol = lower(allow.value.protocol)
      ports    = allow.value.ports
    }
  }

  dynamic "deny" {
    for_each = each.value.action == "DENY" ? each.value.rules : []
    content {
      protocol = lower(deny.value.protocol)
      ports    = deny.value.ports
    }
  }

  lifecycle {
    precondition {
      condition     = contains(["ALLOW", "DENY"], each.value.action)
      error_message = "Firewall action must be ALLOW or DENY."
    }
    precondition {
      condition     = contains(["INGRESS", "EGRESS"], each.value.direction)
      error_message = "Firewall direction must be INGRESS or EGRESS."
    }
  }
}
