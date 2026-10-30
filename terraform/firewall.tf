resource "google_compute_firewall" "rules" {
  for_each = var.firewall_rules

  project       = each.value.project_id
  name          = each.value.name
  network       = each.value.network
  direction     = each.value.direction
  priority      = each.value.priority
  source_ranges = each.value.source_ranges
  target_tags   = each.value.target_tags

  dynamic "allow" {
    for_each = each.value.allowed
    content {
      protocol = allow.value.protocol
      ports    = allow.value.ports
    }
  }

  dynamic "deny" {
    for_each = each.value.denied
    content {
      protocol = deny.value.protocol
      ports    = deny.value.ports
    }
  }
}
